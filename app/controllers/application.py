from calendar import monthrange
from datetime import date
import sqlite3
from types import SimpleNamespace

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def home(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    month_start = date.today().replace(day=1)
    
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
        name="new/app.html",
        context={
            "buckets": buckets,
            "daily_spending_bucket": daily_spending_bucket,
            "other_buckets": other_buckets
        }
    )

