from datetime import datetime, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.models.bucket import Bucket
from app.models.bucket_month_top_up import BucketMonthTopUp


templates = Jinja2Templates(directory="templates")

async def list(request: Request):
    utc_date_today = datetime.now(timezone.utc)

    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))

    month_start = local_date_today.replace(day=1).date()
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
                        SELECT 
                            btu.top_up_id,
                            btu.bucket_id,
                            btu.month_start,
                            btu.start_amount,
                            btu.end_amount,
                            b.name as bucket_name 
                        FROM bucket_month_top_up as btu 
                        JOIN bucket as b 
                        USING (bucket_id)
                        WHERE btu.month_start = ?
                        and b.user_id = ?;
                       """,
                       (month_start, request.state.user.user_id))
        top_ups = [BucketMonthTopUp(**row) for row in cursor.fetchall()]
        
        return templates.TemplateResponse(
        request=request,
        name="hv/bucket/index.xml",
        context={"top_ups": top_ups}
    )
