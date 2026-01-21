from calendar import monthrange
from datetime import datetime, timedelta, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from fastapi import Request
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="templates")

async def index(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"
    return templates.TemplateResponse(
        request=request,
        name="hv/index.xml",
        context={},
        headers={"Content-Type": content_type}
    )


async def login(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    form_data = await request.form()

    previous_values = {}
    errors = {}

    email = form_data.get("email")
    previous_values["email"] = email
    if not email:
        errors["email"] =  "You need to enter your email."

    password = form_data.get("password")
    previous_values["password"] = password
    if not password:
        errors["password"] =  "You need to enter your password."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/auth/form.xml",
            context={
                "previous_values": previous_values,
                "errors": errors
                },
            headers={
                "Content-Type": content_type
                }
        )

    return templates.TemplateResponse(
        request=request,
        name="hv/auth/form.xml",
        context={
            "previous_values": {},
            "errors": {}
            },
        headers={
            "Content-Type": content_type
            }
    )


async def today(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"
    
    # request.state.user = 1
    if not request.state.user:
        return templates.TemplateResponse(
            request=request,
            name="hv/auth/login.xml",
            context={}
        )

    user_id = 1
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    # month_start = local_date_today.replace(month=12, day=1).date()
    month_start = local_date_today.replace(day=1).date()

    local_start_of_day = local_date_today.replace(hour=0, minute=0, second=0)
    utc_start_of_day =  local_start_of_day.astimezone(timezone.utc)

    local_start_of_tomorrow = local_start_of_day + timedelta(days=1)
    utc_start_of_tomorrow =  local_start_of_tomorrow.astimezone(timezone.utc)

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""SELECT bucket_id, name, amount, month_start, is_daily 
                       FROM bucket 
                       WHERE month_start = ? 
                       AND is_daily = ? 
                       AND user_id is ?""", (month_start, 1, user_id))
       
        row = cursor.fetchone()
        if not row:
            return templates.TemplateResponse(
                request=request,
                name="today.html",
                context={
                    "today_date": local_date_today,
                    "purchases": None,
                    "total_spent": None,
                    "daily_spending_bucket": None
                }
            )
        daily_spending_bucket = SimpleNamespace(**row)
        
        cursor.execute("""SELECT purchase.purchase_id,
                            purchase.amount, purchase.currency,
                            purchase.purchased_at, purchase.timezone,
                            purchase.user_id,
                            purchase.bucket_id as bucket_id,
                            bucket.name as bucket_name 
                       FROM purchase
                       JOIN bucket USING (bucket_id)
                       WHERE purchase.user_id = ?
                       AND bucket.is_daily = ?
                       AND purchased_at >= ? AND purchased_at < ?
                       ORDER BY purchased_at DESC;""", (user_id, 1, utc_start_of_day, utc_start_of_tomorrow))
        
        purchases = [SimpleNamespace(**row) for row in cursor.fetchall()]

    if daily_spending_bucket:
        daily_spending_bucket.month = datetime.strptime(daily_spending_bucket.month_start, "%Y-%m-%d")
        daily_spending_bucket.daily_amount = daily_spending_bucket.amount / monthrange(month_start.year, month_start.month)[1]   

    total_spent = 0
    for purchase in purchases:
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))
        total_spent += purchase.amount

    return templates.TemplateResponse(
        request=request,
        name="hv/today.xml",
        context={
            "today_date": local_date_today,
            "purchases": purchases,
            "total_spent": total_spent,
            "daily_spending_bucket": daily_spending_bucket
            },
        headers={"Content-Type": content_type}
    )

async def store(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    form_data = await request.form()

    previous_values = {}
    errors = {}
    
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
    
    currency = form_data.get("currency")
    previous_values["currency"] = currency
    if not currency:
        errors["currency"] = "You need to choose a currency."
    
    # form_date = form_data.get("date")
    # previous_values["date"] = form_date
    # if not form_date:
    #     errors["date"] = "You need to choose a date."
    
    # form_time = form_data.get("time")
    # previous_values["time"] = form_time
    # if not form_time:
    #     errors["time"] = "You need to choose a time."

    form_timezone = form_data.get("timezone")
    previous_values["form_timezone"] = form_timezone
    if not form_timezone:
        errors["timezone"] = "You need to choose a timezone."

    purchased_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/purchases/form.xml",
            context={
                "saved": False,
                "previous_values": previous_values,
                "errors": errors,
                },
            headers={"Content-Type": content_type}
            )

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO purchase (amount, currency, purchased_at, timezone, user_id, bucket_id) VALUES (?, ?, ?, ?, ?, ?);",
                       (amount, currency, purchased_at, form_timezone, 1, bucket_id))
        conn.commit()

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/form.xml",
        context={
            "saved": True,
            "previous_values": {},
            "errors": {},
            },
        headers={"Content-Type": content_type}
        )


async def new(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/new.xml",
        context={},
        headers={"Content-Type": content_type}
        )