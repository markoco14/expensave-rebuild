import asyncio
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import sqlite3
import time
from types import SimpleNamespace
import uuid
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import cryptography
from app.models.bucket import Bucket


templates = Jinja2Templates(directory="templates")

async def show(request: Request, purchase_id: int):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT purchase.purchase_id,
                        purchase.amount,
                        purchase.currency,
                        purchase.purchased_at,
                        purchase.timezone,
                        bucket.name as bucket_name 
                        FROM purchase JOIN bucket USING (bucket_id) 
                        WHERE purchase_id = ?;
                       """,
                       (purchase_id, ))
        purchase = cursor.fetchone()

    if purchase:
        purchase = SimpleNamespace(**purchase)
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/show.xml",
        context={"purchase": purchase},
        headers={"Content-Type": content_type}
    )