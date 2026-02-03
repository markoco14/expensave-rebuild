from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import logging

from fastapi import Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)


async def store(request: Request, bucket_id: int):
    if not request.state.user:
        logger.error("Unauthorized access to bucket.store", bucket_id)
        html = f"<p>You don't have permission to do that. Please check your log in. You may need to <a href='/logout'>Log out</a></p>"
        return HTMLResponse(status_code=200, content=html)
    
    form_data = await request.form()

    month_start = form_data.get("month_start", None)
    if not month_start:
        html = f"<p>Something went wrong with your request. Please try again. You may need to refresh the page.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    start_amount = form_data.get("start_amount", None)
    if not start_amount:
        html = f"<p>You forgot to set your start amount. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    try:
        start_amount = int(start_amount)
    except Exception as e:
        html = f"<p>The amount needs to be a valid number. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    if start_amount <= 0:
        html = f"<p>The amount needs to be a number greater than 0. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)

    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("SELECT bucket_id, is_daily FROM bucket WHERE bucket_id = ?;", (bucket_id, ))
            bucket = cursor.fetchone()
    except Exception as e:
        logger.error("Error retrieving bucket from db:", e)
        html = f"<p>Something went wrong with our server. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    if not bucket:
        logger.error("Bucket not found", bucket_id)
        html = f"<p>We couldn't find a bucket for your top up. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    year = int(month_start.split("-")[0])
    month = int(month_start.split("-")[1])
    _, num_days_in_month = monthrange(year, month)

    if bucket["is_daily"]:
        start_amount = start_amount * num_days_in_month

    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("""
                            INSERT INTO bucket_month_top_up (
                                bucket_id, month_start, start_amount
                            ) VALUES (?, ?, ?);
                           """, (bucket_id, month_start, start_amount))
    except Exception as e:
        logger.error("error inserting top up", e)
        html = f"<p>Something went wrong adding your top up. No balance has been added, please try again.</p>"
        return HTMLResponse(status_code=200, content=html)

    return Response(status_code=200, headers={"hx-reswap": "none", "hx-refresh": "true"})


async def delete(request: Request, top_up_id: int):
    if not request.state.user:
        logger.error("Unauthorized access to top_up.delete", top_up_id)
        html = f"<p>You don't have permission to do that. Please check your log in. You may need to <a href='/logout'>Log out</a></p>"
        return HTMLResponse(status_code=200, content=html)
    
    with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("SELECT top_up_id FROM bucket_month_top_up WHERE top_up_id = ?;", (top_up_id, ))
            top_up = cursor.fetchone()

    if not top_up:
        logger.error("top up not found", top_up_id)
        html = f"<p>We couldn't find the top up. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
    
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("DELETE FROM bucket_month_top_up WHERE top_up_id = ?;", (top_up_id, ))
    except Exception as e:
        logger.error("unable to delete", e)
        html = f"<p>Something went wrong deleting your top up. Please try again.</p>"
        return HTMLResponse(status_code=200, content=html)
        
    return Response(status_code=200, headers={"hx-reswap": "none", "hx-refresh": "true"})