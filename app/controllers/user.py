from datetime import date
import sqlite3
import time
from types import SimpleNamespace
import uuid
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import auth_service

templates = Jinja2Templates(directory="templates")


async def me(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT bucket_id, name, amount, is_daily FROM bucket WHERE user_id = ?;", (request.state.user.user_id, ))
        except Exception as e:
            print(f"something went wrong selecting from the bucket table: {e}")
            return "Internal server error"
        buckets = [SimpleNamespace(**row) for row in cursor.fetchall()]

        budget = cursor.fetchone()
        if budget:
            budget = SimpleNamespace(**budget)
        
    return templates.TemplateResponse(
        request=request,
        name="me.html",
        context={
            "current_user": request.state.user,
            "buckets": buckets,
            "budget": budget,
            "today_date": date.today()
        }
    )