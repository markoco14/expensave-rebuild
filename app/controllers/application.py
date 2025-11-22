from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def today(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    month_start = date.today().replace(day=1)

    utc_date_today = datetime.now(timezone.utc)
    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))
    local_start_of_day = local_date_today.replace(hour=0, minute=0, second=0)
    local_start_of_tomorrow = local_start_of_day + timedelta(days=1)
    utc_start_of_day =  local_start_of_day.astimezone(timezone.utc)
    utc_start_of_tomorrow =  local_start_of_tomorrow.astimezone(timezone.utc)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name, amount, is_daily FROM bucket WHERE month_start = ?", (month_start, ))
        buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]

        cursor.execute("""SELECT purchase.purchase_id,
                            purchase.amount, purchase.currency,
                            purchase.purchased_at, purchase.timezone,
                            purchase.user_id,
                            purchase.bucket_id as bucket_id,
                            bucket.name as bucket_name 
                       FROM purchase
                       JOIN bucket USING (bucket_id)
                       WHERE purchase.user_id = ?
                       AND bucket.name = ?
                       AND purchased_at >= ? AND purchased_at < ?
                       ORDER BY purchased_at DESC;""", (request.state.user.user_id, "Daily Spending", utc_start_of_day, utc_start_of_tomorrow))
        purchases = [SimpleNamespace(**row) for row in cursor.fetchall()]
        
    total_spent = 0
    for purchase in purchases:
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))
        total_spent += purchase.amount

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
        name="today.html",
        context={
            "purchases": purchases,
            "total_spent": total_spent,
            "buckets": buckets,
            "daily_spending_bucket": daily_spending_bucket,
            "other_buckets": other_buckets
        }
    )


async def stats(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)    
    
    return templates.TemplateResponse(
        request=request,
        name="stats.html",
        context={}
    )