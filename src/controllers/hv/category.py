import calendar
from datetime import datetime, timezone
import sqlite3
from typing import Annotated
from zoneinfo import ZoneInfo
from fastapi import Depends, Request, Response
from fastapi.templating import Jinja2Templates

from src.models.bucket import Bucket
from src.models.bucket_month_top_up import BucketMonthTopUp
from src.respository.category import get_with_top_up, list_with_top_ups
from src.respository import purchase_repository as purchase_repo
from src.config import get_db
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

async def list(
        request: Request, 
        conn: Annotated[sqlite3.Connection, Depends(get_db)]
        ):
    current_user = request.state.user
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    month_start = local_date_today.replace(day=1).date()
    
    try:
        category_rows = list_with_top_ups(conn=conn, month_start=month_start, user_id=current_user.user_id)
    except Exception as e:
        logger.error(f"DB error getting categories: {e}", exc_info=True)
        return Response(status_code=500, content="something went wrong on our end")
    
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/index.xml",
        context={
            "categories": category_rows,
            "current_month": month_start
            }
        )


async def show(
        request: Request, 
        conn: Annotated[sqlite3.Connection, Depends(get_db)],
        category_id: int
        ):
    current_user = request.state.user
    if not current_user:
        return Response(status_code=401, content="not authenticated")
    
    try:
        category_row = conn.execute(
            "SELECT * FROM category WHERE category_id = :category_id;", 
            {"category_id": category_id}
            ).fetchone()
    except Exception as e:
        logger.error(f"DB error getting category {category_id}: {e}", exc_info=True)

    return templates.TemplateResponse(
            request=request,
            name="hv/categories/show.xml",
            context={
                "category": category_row
                }
        )
    
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

        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            purchase_rows = purchase_repo.list_for_bucket_and_month(
                conn=conn,
                bucket_id=bucket_id,
                utc_month_start=utc_month_start,
                utc_month_end=utc_month_end
                )

        return templates.TemplateResponse(
            request=request,
            name="hv/categories/_list.xml",
            context={
                "purchases": purchase_rows
            }
        )
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        bucket_top_up_join = get_with_top_up(conn=conn, month_start=month_start, bucket_id=bucket_id)

        logged_spending = purchase_repo.get_logged_spend_for_bucket_month(
            conn=conn,
            bucket_id=bucket_id,
            utc_month_start=utc_month_start,
            utc_month_end=utc_month_end
            )


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
        is_daily=bucket_top_up_join["is_daily"],
        top_up=top_up
    )

    expected_spending = 0
    if bucket.is_daily:
        day_number = datetime.now().day
        number_of_days_finished = day_number
        month_num_days = calendar.monthrange(datetime.now().year, datetime.now().month)[1]
        daily_allowance = int(top_up.start_amount / month_num_days)
        expected_spending = daily_allowance * number_of_days_finished
    

    print(top_up)
    print("start amount", top_up.start_amount)
    print("end amount", top_up.end_amount)

    if top_up.end_amount is None:
        print('no end amount')
        actual_spending = 0

    else:
        if top_up.end_amount == 0:
            actual_spending = top_up.start_amount
        else:
            actual_spending = top_up.start_amount - top_up.end_amount

    print("actual spending", actual_spending)
    return templates.TemplateResponse(
        request=request,
        name="hv/categories/show.xml",
        context={
            "bucket": bucket,
            "top_up": top_up,
            "expected_spending": expected_spending,
            "logged_spending": int(logged_spending),
            "actual_spending": actual_spending
            }
    )