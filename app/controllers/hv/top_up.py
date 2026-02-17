import sqlite3
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket_month_top_up import BucketMonthTopUp

templates = Jinja2Templates(directory="templates")


async def get(
        request: Request, 
        top_up_id: int
        ):
    
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