from datetime import date, datetime, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def me(request: Request):
    if not request.state.user:
        return templates.TemplateResponse(
            request=request,
            name="403.html",
            context={
                "heading": "Permissin denied.",
                "description": "You don't have permission to view this page. Please make sure you are logged in.",
                "link": "login",
                "link_text": "Log in"
            })
    
    utc_date_today = datetime.now(timezone.utc)
    local_date_today = utc_date_today.astimezone(ZoneInfo("Asia/Taipei"))
    month_start = local_date_today.replace(day=1).date()

    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT bucket_id, name, is_daily FROM bucket WHERE user_id = ?;", (request.state.user.user_id, ))
            buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]

            bucket_ids = [str(bucket.bucket_id) for bucket in buckets]
            bucket_ids = ", ".join(bucket_ids)
    
            cursor.execute(f"""
                            SELECT 
                                top_up_id, bucket_id, month_start, start_amount 
                            FROM bucket_month_top_up 
                            WHERE bucket_id 
                            IN ({bucket_ids}) AND month_start = ?;""",
                            (month_start, ))
            
            top_ups = [SimpleNamespace(**row) for row in cursor.fetchall()]

         
    except Exception as e:
        print(f"something went wrong retrieving data: {e}")
        return "Internal server error"
    
    return templates.TemplateResponse(
        request=request,
        name="me.html",
        context={
            "current_user": request.state.user,
            "buckets": buckets,
            "top_ups": top_ups,
        }
    )