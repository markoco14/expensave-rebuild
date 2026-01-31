from datetime import date, datetime, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

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

async def edit(request: Request, purchase_id: int):
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
                        purchase.bucket_id,
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

    month_start = date.today().replace(day=1)
    buckets = Bucket.list_for_month(user_id=request.state.user.user_id, fields=["bucket_id", "name", "is_daily"])

    selected_bucket_id = purchase.bucket_id

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/edit.xml",
        context={
            "purchase": purchase,
            "buckets": buckets,
            "selected_bucket_id": selected_bucket_id
            },
        headers={"Content-Type": content_type}
    )

async def update(request: Request, purchase_id: int):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    form_data = await request.form()
    amount = form_data.get("amount")
    bucket_id = form_data.get("bucket")

    errors = {}
    if not amount:
        errors["amount"] = "You need to include an amount."

    elif not amount.isdigit():
        errors["amount"] = "The amount needs to be a number."

    elif int(amount) <= 0:
        errors["amount"] = "The amoun needs to be more than 0."

    if not bucket_id:
        errors["bucket"] = "You need to choose a bucket"
    elif not bucket_id.isdigit():
        errors["bucket"] = "Invalid bucket selected"
    elif int(bucket_id) <= 0:
        errors["bucket"] = "Invalid bucket selected"

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT purchase.purchase_id,
                        purchase.amount,
                        purchase.currency,
                        purchase.purchased_at,
                        purchase.timezone,
                        purchase.bucket_id,
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


    month_start = date.today().replace(day=1)
    buckets = Bucket.list_for_month(user_id=request.state.user.user_id, fields=["bucket_id", "name", "is_daily"])

    selected_bucket_id = purchase.bucket_id

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/purchases/_form_fields.xml",
            context={
                "purchase": purchase,
                "buckets": buckets,
                "selected_bucket_id": selected_bucket_id,
                "errors": errors
            },
            headers={"Content-Type": content_type}
        )

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE purchase SET amount = ?, bucket_id =? WHERE purchase_id = ?;", (amount, bucket_id, purchase_id))

    purchase.amount = amount
    purchase.bucket_id = bucket_id

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/_form_fields.xml",
        context={
            "saved": True,
            "purchase": purchase,
            "buckets": buckets,
            "selected_bucket_id": selected_bucket_id,
            "errors": {}
        },
        headers={"Content-Type": content_type}
    )



async def delete(request: Request, purchase_id: int):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    if not request.state.user:
        return templates.TemplateResponse(
            request=request,
            name="hv/purchases/_unauthorized.xml",
            context={},
            headers={"Content-Type": content_type}
        )
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM purchase WHERE purchase_id = ?;", (purchase_id, ))

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/_deleted.xml",
        context={},
        headers={"Content-Type": content_type}
    )
