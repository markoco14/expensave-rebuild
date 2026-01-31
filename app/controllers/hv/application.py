import asyncio
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
import time
from types import SimpleNamespace
import uuid
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import cryptography
from app.models.bucket import Bucket


templates = Jinja2Templates(directory="templates")

async def get_today_context(user_id: int):
      
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    # month_start = local_date_today.replace(month=12, day=1).date()
    month_start = local_date_today.replace(day=1).date()

    local_start_of_day = local_date_today.replace(hour=0, minute=0, second=0)
    utc_start_of_day =  local_start_of_day.astimezone(timezone.utc)

    local_start_of_tomorrow = local_start_of_day + timedelta(days=1)
    utc_start_of_tomorrow =  local_start_of_tomorrow.astimezone(timezone.utc)

    buckets = Bucket.list_for_month(user_id=user_id, fields=["bucket_id", "name", "is_daily"])

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("""
                       SELECT b.bucket_id,
                            b.name,
                            b.is_daily,
                            b.user_id,
                            btu.month_start,
                            btu.start_amount
                        FROM bucket b
                        JOIN bucket_month_top_up btu ON b.bucket_id = btu.bucket_id
                        WHERE btu.month_start = ? 
                        AND b.is_daily = 1 
                        AND user_id is ?""", (month_start, user_id))
       
        row = cursor.fetchone()
        if not row:
            context={
                "today_date": local_date_today,
                "purchases": None,
                "total_spent": None,
                "daily_spending_bucket": None,
                "buckets": buckets
            }
            
            return context
        
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
                       ORDER BY purchased_at DESC;""", (user_id, daily_spending_bucket.is_daily, utc_start_of_day, utc_start_of_tomorrow))
        
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

    percent_spent = (total_spent  /  daily_spending_bucket.daily_amount * 100)

    context = {
            "today_date": local_date_today,
            "purchases": purchases,
            "total_spent": total_spent,
            "daily_spending_bucket": daily_spending_bucket,
            "buckets": buckets,
            "percent_spent": percent_spent
            }
    
    return context


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

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email = ?;", (email, ))
        db_user = cursor.fetchone()

    if not db_user:
        errors["email"] =  "You need to enter your email."

    db_user = SimpleNamespace(**db_user)

    if password and not cryptography.verify_password(plain_password=password, hashed_password=db_user.hashed_password):
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
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (token, user_id, expires_at) VALUES (?, ?, ?);", (token, db_user.user_id, expires_at))

    response = templates.TemplateResponse(
        request=request,
        name="hv/auth/form.xml",
        context={
            "saved": True,
            "previous_values": {},
            "errors": {}
            },
        headers={
            "Content-Type": content_type
            }
    )

    response.set_cookie(key="session-id", value=token)

    return response


async def today(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    
    if not request.state.user:
        response = templates.TemplateResponse(
            request=request,
            name="hv/auth/login.xml",
            context={}
        )

        response.delete_cookie("session-id")
        
        return response
    
    context = await get_today_context(user_id=request.state.user.user_id)

    if request.query_params.get("rows_only") and request.query_params.get("rows_only") == "true":
        return templates.TemplateResponse(
            request=request,
            name="hv/_rows.xml",
            context=context,
            headers={"Content-Type": content_type}
        )

    
    return templates.TemplateResponse(
        request=request,
        name="hv/today.xml",
        context=context,
        headers={"Content-Type": content_type}
    )


async def new(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    selected_bucket_id = request.query_params.get("bucket")

    month_start = date.today().replace(day=1)
    
    current_datetime_utc = datetime.now(timezone.utc)
    localized_datetime = current_datetime_utc.astimezone(ZoneInfo("Asia/Taipei"))

    # default_date = localized_datetime.date()
    # default_time = localized_datetime.time().strftime("%H:%M:%S")

    buckets = Bucket.list_for_month(month_start=month_start, user_id=request.state.user.user_id, fields=["bucket_id", "name", "amount", "is_daily"])

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/new.xml",
        context={
            "saved": False,
            "selected_bucket_id": selected_bucket_id,
            "previous_values": {},
            "errors": {},
            "buckets": buckets
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
    selected_bucket_id = bucket_id
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
    
    # form_date = form_data.get("date")
    # previous_values["date"] = form_date
    # if not form_date:
    #     errors["date"] = "You need to choose a date."
    
    # form_time = form_data.get("time")
    # previous_values["time"] = form_time
    # if not form_time:
    #     errors["time"] = "You need to choose a time."

    # form_timezone = form_data.get("timezone")
    # previous_values["form_timezone"] = form_timezone
    # if not form_timezone:
    #     errors["timezone"] = "You need to choose a timezone."

    purchased_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    month_start = date.today().replace(day=1)
    
    current_datetime_utc = datetime.now(timezone.utc)
    localized_datetime = current_datetime_utc.astimezone(ZoneInfo("Asia/Taipei"))

    buckets = Bucket.list_for_month(month_start=month_start, user_id=request.state.user.user_id, fields=["bucket_id", "name", "amount", "is_daily"])

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/purchases/form.xml",
            context={
                "saved": False,
                "previous_values": previous_values,
                "errors": errors,
                "buckets": buckets,
                "selected_bucket_id": selected_bucket_id
                },
            headers={"Content-Type": content_type}
            )

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO purchase (amount, currency, purchased_at, timezone, user_id, bucket_id) VALUES (?, ?, ?, ?, ?, ?);",
                       (amount, "TWD", purchased_at, "Asia/Taipei", request.state.user.user_id, bucket_id))
        conn.commit()

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/form.xml",
        context={
            "saved": True,
            "previous_values": {},
            "errors": {},
            "buckets": buckets,
            "selected_bucket_id": selected_bucket_id
            },
        headers={"Content-Type": content_type}
        )
