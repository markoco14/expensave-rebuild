from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def today(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
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
                       AND user_id is ?""", (month_start, 1, request.state.user.user_id))
       
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
                       ORDER BY purchased_at DESC;""", (request.state.user.user_id, 1, utc_start_of_day, utc_start_of_tomorrow))
        
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
        name="today.html",
        context={
            "today_date": local_date_today,
            "purchases": purchases,
            "total_spent": total_spent,
            "daily_spending_bucket": daily_spending_bucket
        }
    )


async def stats(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    month_start = date.today().replace(day=1)
    
    query_params = request.query_params
    start_date = None
    end_date = None
    if query_params:
        start_date = query_params.get("start_date")
        end_date = query_params.get("end_date")
        
    if not start_date and not end_date:
        utc_date_today = datetime.now(timezone.utc)
        utc_start_of_month = utc_date_today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        utc_end_of_month = utc_date_today.replace(day=monthrange(utc_start_of_month.year, utc_start_of_month.month)[1], hour=23, minute=59, second=59, microsecond=99999)

        utc_start_of_next_month = utc_start_of_month.replace(day=monthrange(utc_start_of_month.year, utc_start_of_month.month)[1], hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
 
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()

            cursor.execute("SELECT * FROM bucket WHERE user_id = ? AND is_daily = ? AND month_start = ?;", (request.state.user.user_id, 1, month_start))

            row = cursor.fetchone()
            if not row:
                return templates.TemplateResponse(
                    request=request,
                    name="stats.html",
                    context={
                        "bucket": None,
                        "purchases": [],
                        "amount_remaining": None,
                        "amount_in_time_period": None,
                        "total_spent_in_period": None,
                        "start_value": utc_start_of_month.strftime("%Y-%m-%d"),
                        "end_value": utc_end_of_month.strftime("%Y-%m-%d"),
                    }
                )
            
            bucket = SimpleNamespace(**row)

            cursor.execute("""SELECT purchase.purchase_id,
                            purchase.amount, purchase.currency,
                            purchase.purchased_at, purchase.timezone,
                            purchase.user_id,
                            purchase.bucket_id as bucket_id,
                            bucket.name as bucket_name, bucket.amount as bucket_amount  
                        FROM purchase
                        JOIN bucket USING (bucket_id)
                        WHERE purchase.user_id = ?
                        AND bucket.name = ?
                        AND purchased_at >= ? AND purchased_at < ?
                        ORDER BY purchased_at DESC;""",
                        (request.state.user.user_id, bucket.name, utc_start_of_month, utc_start_of_next_month))
            
            rows = cursor.fetchall()

        purchases = [SimpleNamespace(**row) for row in rows]

        total_spent_in_period = 0
        for purchase in purchases:
            total_spent_in_period += purchase.amount

        return templates.TemplateResponse(
            request=request,
            name="stats.html",
            context={
                "bucket": bucket,
                "purchases": purchases,
                "amount_remaining": None,
                "amount_in_time_period": None,
                "total_spent_in_period": total_spent_in_period,
                "start_value": utc_start_of_month.strftime("%Y-%m-%d"),
                "end_value": utc_end_of_month.strftime("%Y-%m-%d"),
            }
        )

    time_period_start = datetime.strptime(start_date, "%Y-%m-%d")
    time_period_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

    # Convert strings to datetime objects
    number_of_days = None
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        # Calculate the difference and get the number of days
        number_of_days = (end - start).days + 1

    days_in_period = 100
    if number_of_days:
        days_in_period = number_of_days

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bucket WHERE user_id = ? AND is_daily = ?;", (request.state.user.user_id, 1))

        row = cursor.fetchone()
        if not row:
            return templates.TemplateResponse(
                request=request,
                name="stats.html",
                context={
                    "bucket": None,
                    "purchases": [],
                    "amount_remaining": None,
                    "amount_in_time_period": None,
                    "total_spent_in_period": None,
                    "start_value": time_period_start.strftime("%Y-%m-%d"),
                    "end_value": time_period_end.strftime("%Y-%m-%d"),
                }
            )
        
        bucket = SimpleNamespace(**row)

        cursor.execute("""SELECT purchase.purchase_id,
                        purchase.amount, purchase.currency,
                        purchase.purchased_at, purchase.timezone,
                        purchase.user_id,
                        purchase.bucket_id as bucket_id,
                        bucket.name as bucket_name, bucket.amount as bucket_amount  
                    FROM purchase
                    JOIN bucket USING (bucket_id)
                    WHERE purchase.user_id = ?
                    AND bucket.name = ?
                    AND purchased_at >= ? AND purchased_at <= ?
                    ORDER BY purchased_at DESC;""",
                    (request.state.user.user_id, bucket.name, time_period_start, time_period_end))
        
        rows = cursor.fetchall()

    purchases = [SimpleNamespace(**row) for row in rows]
    
    total_spent_in_period = 0
    for purchase in purchases:
        total_spent_in_period += purchase.amount

    num_days_bucket_amount = bucket.amount / 100 * days_in_period
    
    amount_remaining = num_days_bucket_amount - total_spent_in_period
    
    return templates.TemplateResponse(
        request=request,
        name="stats.html",
        context={
            "bucket": bucket,
            "purchases": purchases,
            "amount_remaining": amount_remaining,
            "amount_in_time_period": None,
            "total_spent_in_period": total_spent_in_period,
            "start_value": time_period_start.strftime("%Y-%m-%d"),
            "end_value": time_period_end.strftime("%Y-%m-%d"),
        }
    )

async def delete_toast():
    return Response(status_code=200)
