from datetime import date, datetime, timezone
import sqlite3
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.templating import Jinja2Templates

from src.config import get_db
from src.models.bucket import Bucket
from src.respository import purchase_repository

templates = Jinja2Templates(directory="templates")


async def show(request: Request, purchase_id: int):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    try:
        with get_db() as conn:
            purchase = purchase_repository.get(conn=conn, purchase_id=purchase_id)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="hv/server-error.xml",
            context={},
            headers={"Content-Type": content_type}
        )

    if not purchase:
        return templates.TemplateResponse(
            request=request,
            name="hv/404.xml",
            context={},
            headers={"Content-Type": content_type}
        )
    
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

    with get_db() as conn:
        purchase = purchase_repository.get(conn=conn, purchase_id=purchase_id)

    if purchase:
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/edit.xml",
        context={
            "purchase": purchase,
            },
        headers={"Content-Type": content_type}
    )


async def update(request: Request, purchase_id: int):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    form_data = await request.form()
    amount = form_data.get("amount")

    errors = {}
    if not amount:
        errors["amount"] = "You need to include an amount."

    elif not amount.isdigit():
        errors["amount"] = "The amount needs to be a number."

    elif int(amount) <= 0:
        errors["amount"] = "The amoun needs to be more than 0."

    with get_db() as conn:
        purchase = purchase_repository.get(conn=conn, purchase_id=purchase_id)

    if purchase:
        naive = datetime.strptime(purchase.purchased_at, "%Y-%m-%d %H:%M:%S")
        utc_aware = naive.replace(tzinfo=timezone.utc)
        purchase.purchased_at = utc_aware.astimezone(ZoneInfo(purchase.timezone))

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/purchases/_old-form-fields.xml",
            context={
                "purchase": purchase,                
                "errors": errors
            },
            headers={"Content-Type": content_type}
        )

    with get_db() as conn:
        conn.execute(
            "UPDATE purchase SET amount = ? WHERE purchase_id = ?;", 
            (amount, purchase_id))
        conn.commit()

    purchase.amount = amount

    return templates.TemplateResponse(
        request=request,
        name="hv/purchases/_old-form-fields.xml",
        context={
            "saved": True,
            "purchase": purchase,            
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
