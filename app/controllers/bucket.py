import sqlite3
import time
from types import SimpleNamespace
import uuid
from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import auth_service

templates = Jinja2Templates(directory="templates")


def delete(request: Request, bucket_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bucket WHERE bucket_id = ?;", (bucket_id,))
    
    response = Response(status_code=204, headers={"hx-refresh": "true"})
    return response

