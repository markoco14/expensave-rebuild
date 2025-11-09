from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

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
    
    month_start = date.today().replace(day=1)
    current_datetime_utc = datetime.now(timezone.utc)
    localized_datetime = current_datetime_utc.astimezone(ZoneInfo("Asia/Taipei"))

    default_date = localized_datetime.date()
    default_time = localized_datetime.time().strftime("%H:%M:%S")
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name, amount, is_daily FROM bucket WHERE month_start = ?", (month_start, ))
        buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]

    daily_spending_bucket = None
    other_buckets = []
    for bucket in buckets:
        if bucket.is_daily == True:
            daily_spending_bucket = bucket
            daily_spending_bucket.daily_amount = bucket.amount / monthrange(month_start.year, month_start.month)[1]   
        else:
            other_buckets.append(bucket)
    
    return templates.TemplateResponse(
        request=request,
        name="purchases/new.html",
        context={
            "buckets": buckets,
            "daily_spending_bucket": daily_spending_bucket,
            "other_buckets": other_buckets,
            "default_date": default_date,
            "default_time": default_time
        }
    )


async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    form_data = await request.form()

    bucket_id = form_data.get("bucket")
    if not bucket_id:
        return RedirectResponse(url="/app", status_code=303)

    amount = form_data.get("amount")
    if not amount:
        return "You need to choose an amount."
    
    if not amount.isdigit():
        return "The amount needs to be a number."
    
    if int(amount) == 0:
        return "The amount needs to be more than 0."
    
    currency = form_data.get("currency")
    if not currency:
        return "You need to choose a currency."
    
    date = form_data.get("date")
    if not date:
        return "You need to choose a date."
    
    time = form_data.get("time")
    if not time:
        return "You need to choose a time."

    form_timezone = form_data.get("timezone")
    if not form_timezone:
        return "You need to choose a timezone."
    
    local_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
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
    
    return RedirectResponse(url="/purchases", status_code=303)


async def show(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
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

    if not purchase:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={
                "header": "Purchase Not Found",
                "apology": "We are sorry, but we were unable to find your purchase.",
                "link": "purchases",
                "link_text": "Back to purchases"
            },
            status_code=404
        )

    if request.state.user.user_id != purchase.user_id:
        return RedirectResponse(url="/login", status_code=303)
    
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

    if not purchase:
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

    if request.state.user.user_id != purchase.user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name FROM bucket WHERE user_id = ?;", (request.state.user.user_id,))
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

    if not purchase:
        return Response(status_code=404, headers={"hx-refresh": "/true"})

    if request.state.user.user_id != purchase.user_id:
        if request.headers.get("hx-request"):
            return Response(status_code=404, headers={"hx-redirect": "/login"})
        return RedirectResponse(url="/login", status_code=303)
    
    local_naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    local_tz_aware = local_naive.replace(tzinfo=ZoneInfo(form_timezone))
    utc_time = local_tz_aware.astimezone(timezone.utc)
    utc_naive = utc_time.replace(tzinfo=None)

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("UPDATE purchase SET amount = ?, purchased_at = ?, bucket_id = ? WHERE purchase_id = ?;", (amount, utc_naive, bucket, purchase_id))

    response = Response(headers={"hx-refresh": "true"})
    return response


async def delete(request: Request, purchase_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase WHERE purchase_id = ?;", (purchase_id,))
        row = cursor.fetchone()
        purchase = SimpleNamespace(**row) if row else None

    if not purchase:
        return Response(status_code=404, headers={"hx-redirect": "/purchases"})
    
    if request.state.user.user_id != purchase.user_id:
        if request.headers.get("hx-request"):
            return Response(status_code=404, headers={"hx-redirect": "/purchases"})
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("DELETE FROM purchase WHERE purchase_id = ?;", (purchase_id, ))

    response = Response(headers={"hx-redirect": "/purchases"})
    return response