from calendar import monthrange
from datetime import date, datetime, timedelta
import sqlite3
from types import SimpleNamespace
from fastapi import Request
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
        cursor.execute("SELECT * FROM purchase WHERE user_id = ? ORDER BY purchased_at DESC;", (request.state.user.user_id, ))
        purchases = [SimpleNamespace(**row) for row in cursor.fetchall()]

    return templates.TemplateResponse(
        request=request,
        name="new/purchases/index.html",
        context={"purchases": purchases}
    )

async def new(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    month_start = date.today().replace(day=1)
    current_datetime = datetime.now()
    default_date = current_datetime.date()
    default_time = current_datetime.time().strftime("%H:%M:%S")
    
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
        name="new/purchases/new.html",
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

    timezone = form_data.get("timezone")
    if not timezone:
        return "You need to choose a timezone."
    
    local_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    utc_time = local_time - timedelta(hours=8)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO purchase (amount, currency, purchased_at, timezone, user_id, bucket_id) VALUES (?, ?, ?, ?, ?, ?);", (amount, currency, utc_time, timezone, request.state.user.user_id, bucket_id))
        except Exception as e:
            print(f"something went wrong storing the purchase: {e}")
            return "Something went wrong on our server."
    
    return RedirectResponse(url="/purchases", status_code=303)
