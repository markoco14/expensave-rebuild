from datetime import datetime, timezone
from pprint import pprint
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket import Bucket
from app.models.bucket_month_top_up import BucketMonthTopUp
from app.respository.bucket import get_with_top_up, list_with_top_ups


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


async def show(request: Request, bucket_id: int):
    query_params = request.query_params
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    # for debugging
    # local_date_today = local_date_today.replace(month=12)

    local_start_of_month_datetime = local_date_today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    local_end_of_month_datetime = None
    if local_date_today.month == 12:
        # print('twelfth month detected')
        local_end_of_month_datetime = local_start_of_month_datetime.replace(year=local_date_today.year + 1, month=1)
    else:
        # print('not twelfth month')
        local_end_of_month_datetime = local_start_of_month_datetime.replace(month=local_date_today.month + 1)

    utc_month_start = local_start_of_month_datetime.astimezone(timezone.utc)
    utc_month_end = local_end_of_month_datetime.astimezone(timezone.utc)

    month_start = local_date_today.replace(day=1).date()

    # get start and end of month
    if query_params.get("content") == "list":

        # get the bucket by the top up
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                            SELECT 
                                b.bucket_id, 
                                b.name,
                                btu.top_up_id,
                                btu.month_start
                            FROM bucket as b 
                            JOIN bucket_month_top_up as btu
                            USING (bucket_id)
                            WHERE bucket_id = ?
                            AND month_start = ?;
                            """, (bucket_id, month_start))
            row = cursor.fetchone()

            if not row:
                return templates.TemplateResponse(
                    request=request,
                    name="hv/top-up/list.xml",
                    context={
                        "purchases": []
                    }
                )

            cursor.execute("""
                           SELECT * 
                           FROM purchase 
                           WHERE bucket_id = ?
                           AND purchased_at >= ?
                           AND purchased_at < ?
                           ORDER BY purchased_at DESC;""", (row["bucket_id"], utc_month_start, utc_month_end))
            
            purchase_rows = cursor.fetchall()

        return templates.TemplateResponse(
            request=request,
            name="hv/top-up/list.xml",
            context={
                "purchases": purchase_rows
            }
        )
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        bucket_top_up_join = get_with_top_up(conn=conn, month_start=month_start, bucket_id=bucket_id)

    if not bucket_top_up_join:
        return templates.TemplateResponse(
            request=request,
            name="hv/404.xml",
            context={}
        )
    
    top_up = BucketMonthTopUp(
        top_up_id=bucket_top_up_join["top_up_id"],
        month_start=bucket_top_up_join["month_start"],
        start_amount=bucket_top_up_join["start_amount"],
        end_amount=bucket_top_up_join["end_amount"]
        )
    
    bucket = Bucket(
        bucket_id=bucket_top_up_join["bucket_id"],
        name=bucket_top_up_join["name"],
        top_up=top_up
    )

    return templates.TemplateResponse(
        request=request,
        name="hv/top-up/show.xml",
        context={
            "top_up": None,
            "bucket": bucket
            }
    )