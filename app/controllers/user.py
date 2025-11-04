from datetime import date
import sqlite3
import time
from types import SimpleNamespace
import uuid
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import auth_service

templates = Jinja2Templates(directory="templates")


async def me(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, name FROM bucket WHERE user_id = ?;", (request.state.user.user_id, ))
        buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]

        cursor.execute("SELECT budget_id, amount FROM budget WHERE user_id = ? AND ended_at IS NULL;", (request.state.user.user_id,))
        budget = cursor.fetchone()
        if budget:
            budget = SimpleNamespace(**budget)
        
    return templates.TemplateResponse(
        request=request,
        name="new/me.html",
        context={
            "current_user": request.state.user,
            "buckets": buckets,
            "budget": budget,
            "today_date": date.today()
        }
    )