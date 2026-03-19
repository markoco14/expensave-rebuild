from datetime import datetime, timedelta, timezone
import sqlite3
from zoneinfo import ZoneInfo
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket_month_top_up import BucketMonthTopUp

templates = Jinja2Templates(directory="templates")


async def show(request: Request, top_up_id: int):
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
                            WHERE top_up_id = ?
                            AND month_start = ?;
                            """, (top_up_id, month_start))
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
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT 
                            btu.top_up_id, 
                            btu.month_start, 
                            btu.start_amount, 
                            btu.end_amount,
                            b.name as bucket_name 
                        FROM bucket_month_top_up as btu
                        JOIN bucket as b
                        USING (bucket_id)
                        WHERE top_up_id = ?;
                       """, (top_up_id, ))
        top_up = cursor.fetchone()

    if not top_up:
        return templates.TemplateResponse(
            request=request,
            name="hv/404.xml",
            context={}
        )
    
    top_up = BucketMonthTopUp(**top_up)

    return templates.TemplateResponse(
        request=request,
        name="hv/top-up/show.xml",
        context={
            "top_up": top_up
            }
    )

async def edit(request: Request, top_up_id: int):
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT 
                            btu.top_up_id, 
                            btu.month_start, 
                            btu.start_amount, 
                            btu.end_amount,
                            b.name as bucket_name 
                        FROM bucket_month_top_up as btu
                        JOIN bucket as b
                        USING (bucket_id)
                        WHERE top_up_id = ?;
                       """, (top_up_id, ))
        top_up = cursor.fetchone()

    if not top_up:
        return templates.TemplateResponse(
            request=request,
            name="hv/404.xml",
            context={}
        )
    top_up = BucketMonthTopUp(**top_up)

    return templates.TemplateResponse(
        request=request,
        name="hv/top-up/edit.xml",
        context={
            "top_up": top_up
            }
    )

async def update(request: Request, top_up_id: int):
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT 
                            btu.top_up_id, 
                            btu.month_start, 
                            btu.start_amount, 
                            btu.end_amount,
                            b.name as bucket_name 
                        FROM bucket_month_top_up as btu
                        JOIN bucket as b
                        USING (bucket_id)
                        WHERE top_up_id = ?;
                       """, (top_up_id, ))
        top_up = cursor.fetchone()

    if not top_up:
        return templates.TemplateResponse(
            request=request,
            name="hv/404.xml",
            context={}
        )
    
    form_data = await request.form()
    start_amount = form_data.get("start_amount", None)
    end_amount = form_data.get("end_amount", None)
    
    if not start_amount or not end_amount:
        return templates.TemplateResponse(
            request=request,
            name="hv/top-up/_form_fields.xml",
            context={
                "top_up": top_up
                }
        )
    
    try:
        int(start_amount)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="hv/top-up/_form_fields.xml",
            context={
                "top_up": top_up
                }
        )
    
    try:
        int(end_amount)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="hv/top-up/_form_fields.xml",
            context={
                "top_up": top_up
                }
        )
    

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("UPDATE bucket_month_top_up SET start_amount = ?, end_amount = ? WHERE top_up_id = ?;", (start_amount, end_amount, top_up_id))

    top_up = BucketMonthTopUp(**top_up)
    top_up.start_amount = start_amount
    top_up.end_amount = end_amount

    return templates.TemplateResponse(
        request=request,
        name="hv/top-up/_form_fields.xml",
        context={
            "saved": True,
            "top_up": top_up
            }
    )