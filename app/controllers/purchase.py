from calendar import monthrange
from datetime import date, datetime, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.bucket import Bucket

templates = Jinja2Templates(directory="templates")


async def list(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""SELECT purchase.purchase_id,
                            purchase.amount, purchase.currency,
                            purchase.purchased_at, purchase.timezone,
                            purchase.user_id,
                            purchase.bucket_id as bucket_id,
                            bucket.name as bucket_name
                        FROM purchase
                        JOIN bucket USING (bucket_id)
                        WHERE purchase.user_id = ?
                        ORDER BY purchased_at DESC;""", (request.state.user.user_id, ))
        purchases = [SimpleNamespace(**row) for row in cursor.fetchall()]

    for purchase in purchases:
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))

    return templates.TemplateResponse(
        request=request,
        name="purchases/index.html",
        context={"purchases": purchases}
    )


async def new(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    current_datetime_utc = datetime.now(timezone.utc)
    localized_datetime = current_datetime_utc.astimezone(ZoneInfo("Asia/Taipei"))

    default_date = localized_datetime.date()
    default_time = localized_datetime.time().strftime("%H:%M:%S")

    buckets = Bucket.list_for_month(user_id=request.state.user.user_id, fields=["bucket_id, name, is_daily"])

    return templates.TemplateResponse(
        request=request,
        name="purchases/new.html",
        context={
            "buckets": buckets,
            "default_date": default_date,
            "default_time": default_time,
            "errors": {},
            "previous_values": {}
        }
    )


async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)

    form_data = await request.form()

    previous_values = {}
    errors = {}
    currency = "TWD"
    form_timezone = "Asia/Taipei"
    
    bucket_id = form_data.get("bucket")
    previous_values["bucket"] = bucket_id
    if not bucket_id:
        errors["bucket"] =  "You need to choose a bucket."

    amount = form_data.get("amount")
    previous_values["amount"] = amount
    if not amount:
        errors["amount"] = "You need to choose an amount."
    else:
        if not amount.isdigit():
            errors["amount"] = "The amount needs to be a number."

        elif int(amount) < 1:
            errors["amount"] = "The amount needs to be more than 0."
    
    # currency = form_data.get("currency")
    # previous_values["currency"] = currency
    # if not currency:
    #     errors["currency"] = "You need to choose a currency."
    
    form_date = form_data.get("date")
    previous_values["date"] = form_date
    if not form_date:
        errors["date"] = "You need to choose a date."
    
    form_time = form_data.get("time")
    previous_values["time"] = form_time
    if not form_time:
        errors["time"] = "You need to choose a time."

    # form_timezone = form_data.get("timezone")
    # previous_values["form_timezone"] = form_timezone
    # if not form_timezone:
    #     errors["timezone"] = "You need to choose a timezone."

    if errors:
        month_start = date.today().replace(day=1)
        current_datetime_utc = datetime.now(timezone.utc)
        localized_datetime = current_datetime_utc.astimezone(ZoneInfo("Asia/Taipei"))

        default_date = localized_datetime.date()
        default_time = localized_datetime.time().strftime("%H:%M:%S")
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("SELECT bucket_id, is_daily, name FROM bucket WHERE user_id = ?;", (request.state.user.user_id, ))
            buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]
            
      

        return templates.TemplateResponse(
            request=request,
            name="purchases/new.html",
            context={
                "buckets": buckets,
                "default_date": default_date,
                "default_time": default_time,
                "errors": errors,
                "previous_values": previous_values
            },
            headers={"hx-retarget": "body", "hx-reswap": "outerHTML"}
        )
    
    local_naive = datetime.strptime(f"{form_date} {form_time}", "%Y-%m-%d %H:%M:%S")
    local_tz_aware = local_naive.replace(tzinfo=ZoneInfo(form_timezone))
    utc_time = local_tz_aware.astimezone(timezone.utc)
    utc_naive = utc_time.replace(tzinfo=None)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO purchase (amount, currency, purchased_at, timezone, user_id, bucket_id) VALUES (?, ?, ?, ?, ?, ?);", (amount, currency, utc_naive, form_timezone, request.state.user.user_id, bucket_id))
        except Exception as e:
            print(f"something went wrong storing the purchase: {e}")
            return "Something went wrong on our server."
        
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"hx-redirect": "/purchases"})
    
    return RedirectResponse(url="/purchases", status_code=303)


async def show(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not request.state.purchase:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "heading": "Purchase Not Found",
                "apology": "We are sorry, but we were unable to find your purchase.",
                "link": "purchases",
                "link_text": "Back to purchases"
            },
            status_code=404
        )
    
    if request.state.purchase.user_id != request.state.user.user_id:
        return templates.TemplateResponse(
            request=request,
            name="403.html",
            context={
                "heading": "Permission Denied",
                "apology": "We are sorry, but this purchase belongs to someone else.",
                "link": "purchases",
                "link_text": "Back to purchases"
            },
            status_code=403
        )
    
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
                    SELECT purchase.purchase_id, purchase.amount,
                        purchase.currency, purchase.purchased_at,
                        purchase.timezone, purchase.user_id,
                        purchase.bucket_id as bucket_id,
                        bucket.name as bucket_name 
                    FROM purchase 
                    JOIN bucket USING (bucket_id) 
                    WHERE purchase.user_id = ? AND purchase.purchase_id = ?;""", (request.state.user.user_id, purchase_id))
        row = cursor.fetchone()
        purchase = SimpleNamespace(**row) if row else None
    
    naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
    utc_aware = naive.replace(tzinfo=timezone.utc)
    purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))

    return templates.TemplateResponse(
        request=request,
        name="purchases/show.html",
        context={"purchase": purchase}
    )


async def edit(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not request.state.purchase:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "heading": "Purchase Not Found",
                "apology": "We are sorry, but we were unable to find your purchase.",
                "link": "purchases",
                "link_text": "Back to purchases"
            },
            status_code=404
        )
    
    if request.state.purchase.user_id != request.state.user.user_id:
        return templates.TemplateResponse(
            request=request,
            name="403.html",
            context={
                "heading": "Permission Denied",
                "apology": "We are sorry, but this purchase belongs to someone else.",
                "link": "purchases",
                "link_text": "Back to purchases"
            },
            status_code=403
        )
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
                    SELECT purchase.purchase_id, purchase.amount,
                        purchase.currency, purchase.purchased_at,
                        purchase.timezone, purchase.user_id,
                        purchase.bucket_id as bucket_id,
                        bucket.name as bucket_name 
                    FROM purchase 
                    JOIN bucket USING (bucket_id) 
                    WHERE purchase.user_id = ? AND purchase.purchase_id = ?;""", (request.state.user.user_id, purchase_id))
        row = cursor.fetchone()
        purchase = SimpleNamespace(**row) if row else None
    
    month_start = date.today().replace(day=1)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name FROM bucket WHERE user_id = ?;", (request.state.user.user_id, ))
        buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]
    
    naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
    utc_aware = naive.replace(tzinfo=timezone.utc)
    purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))
    
    return templates.TemplateResponse(
        request=request,
        name="purchases/edit.html",
        context={"purchase": purchase, "buckets": buckets}
    )


async def update(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not request.state.purchase:
        return Response(status_code=404, headers={"hx-refresh": "/true"})
    
    if request.state.purchase.user_id != request.state.user.user_id:
        return Response(status_code=403, headers={"hx-refresh": "/true"})
    
    form_data = await request.form()

    amount = form_data.get("amount")
    if not amount:
        return "You need to choose an amount"
    
    date = form_data.get("date")
    if not date:
        return "You need to choose a date"
    
    time = form_data.get("time")
    if not time:
        return "You need to choose a time"
    
    form_timezone = form_data.get("timezone")
    if not form_timezone:
        return "You need to choose a timezone."
    
    bucket = form_data.get("bucket")
    if not bucket:
        return "You need to choose a bucket"
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase WHERE purchase_id = ?;", (purchase_id,))
        row = cursor.fetchone()
        purchase = SimpleNamespace(**row) if row else None
    
    local_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    local_tz_aware = local_naive.replace(tzinfo=ZoneInfo(form_timezone))
    utc_time = local_tz_aware.astimezone(timezone.utc)
    utc_naive = utc_time.replace(tzinfo=None)

    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("UPDATE purchase SET amount = ?, purchased_at = ?, bucket_id = ? WHERE purchase_id = ?;", (amount, utc_naive, bucket, purchase_id))

        html = "<div class='toast success' hx-delete='/toast/delete' hx-trigger='load delay:1.5s' hx-swap='outerHTML swap:300ms'><p>Purchase info updated</p></div>"
        return HTMLResponse(status_code=200, content=html, headers={"hx-retarget": "body", "hx-reswap": "afterbegin"})
    except Exception as e:
        html = "<div class='toast failure' hx-delete='/toast/delete' hx-trigger='load delay:1.5s' hx-swap='outerHTML swap:300ms'><p>Something went wrong</p></div>"
        return HTMLResponse(status_code=200, content=html, headers={"hx-retarget": "body", "hx-reswap": "afterbegin"})

async def delete(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    if not request.state.purchase:
        html = "<div class='toast failure' hx-delete='/toast/delete' hx-trigger='load delay:1.5s' hx-swap='outerHTML swap:300ms'><p>Purchase not found</p></div>"
        return HTMLResponse(status_code=200, content=html, headers={"hx-retarget": "body", "hx-reswap": "afterbegin"})
    
    if request.state.purchase.user_id != request.state.user.user_id:
        html = "<div class='toast failure' hx-delete='/toast/delete' hx-trigger='load delay:1.5s' hx-swap='outerHTML swap:300ms'><p>You don't have permission to delete this purchase</p></div>"
        return HTMLResponse(status_code=200, content=html, headers={"hx-retarget": "body", "hx-reswap": "afterbegin"})
    
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("DELETE FROM purchase WHERE purchase_id = ?;", (purchase_id, ))
        return Response(headers={"hx-redirect": "/purchases"})
    except Exception as e:
        html = "<div class='toast failure' hx-delete='/toast/delete' hx-trigger='load delay:1.5s' hx-swap='outerHTML swap:300ms'><p>Something went wrong deleting the purchase</p></div>"
        return HTMLResponse(status_code=200, content=html, headers={"hx-retarget": "body", "hx-reswap": "afterbegin"})
