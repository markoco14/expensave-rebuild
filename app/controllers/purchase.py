import sqlite3
from types import SimpleNamespace
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

async def list(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM purchase WHERE user_id = ?;", (request.state.user.user_id, ))
        purchases = [SimpleNamespace(**row) for row in cursor.fetchall()]

    return templates.TemplateResponse(
        request=request,
        name="new/purchases/index.html",
        context={"purchases": purchases}
    )


async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    form_data = await request.form()

    bucket_id = form_data.get("bucket")
    if not bucket_id:
        return RedirectResponse(url="/app", status_code=303)

    amount = form_data.get("amount")
    if not amount:
        return "You need to choose an amount"
    
    if not amount.isdigit():
        return "The amount needs to be a number"
    
    if int(amount) == 0:
        return "The amount needs to be more than 0"
    
    return "created"