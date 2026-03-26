from datetime import datetime, timezone
from pprint import pprint
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket import Bucket
from app.models.bucket_month_top_up import BucketMonthTopUp
from app.respository.bucket import list_with_top_ups


templates = Jinja2Templates(directory="templates")

async def list(request: Request):
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    month_start = local_date_today.replace(day=1).date()
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        bucket_rows = list_with_top_ups(conn=conn, month_start=month_start, user_id=request.state.user.user_id)
    
    buckets = []
    for row in bucket_rows:
        top_up = BucketMonthTopUp(
            top_up_id = row["top_up_id"],
            month_start=row["month_start"],
            start_amount=row["start_amount"],
            end_amount=row["end_amount"]
        )

        bucket = Bucket(
            bucket_id=row["bucket_id"],
            name=row["name"],
            top_up=top_up
        )

        buckets.append(bucket)
        
    return templates.TemplateResponse(
        request=request,
        name="hv/bucket/index.xml",
        context={
            "buckets": buckets,
            "current_month": month_start
            }
        )
