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



async def today(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"
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