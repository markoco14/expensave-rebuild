import sqlite3
import time
from types import SimpleNamespace
import uuid
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import auth_service

templates = Jinja2Templates(directory="templates")



async def create(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    form_data = await request.form()

    bucket_name = form_data.get("bucket")

    if not bucket_name:
        return "You need a bucket name"
    
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO bucket (user_id, name) VALUES (?, ?);", (request.state.user.user_id, bucket_name))
        except Exception as e:
            return f"You already have a {bucket_name} bucket."
    
    return RedirectResponse(url="/me", status_code=303)


def delete(request: Request, bucket_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()
        cursor.execute("SELECT bucket_id, user_id FROM bucket WHERE bucket_id = ?;", (bucket_id,))

        bucket = cursor.fetchone()
        if not bucket:
            return "There is no bucket"

        if bucket["user_id"] != request.state.user.user_id:
            return "You are not the right user"
        
        cursor.execute("DELETE FROM bucket WHERE bucket_id = ?;", (bucket_id,))
    
    response = Response(status_code=204, headers={"hx-refresh": "true"})
    return response

