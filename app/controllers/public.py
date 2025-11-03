import sqlite3
import time
import uuid
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.auth import auth_service

templates = Jinja2Templates(directory="templates")


def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new/index.html",
        context={}
    )

def signup(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new/signup.html",
        context={}
    )

async def register(request: Request):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")

    if not email:
        return "no email"
    
    if not password:
        return "no password"
    
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE email = ?;", (email, ))
        db_user = cursor.fetchone()

    if db_user:
        return "user exists"

    if not db_user:
        hashed_password = auth_service.get_password_hash(password)
        with sqlite3.connect("db.sqlite3") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user (email, hashed_password) VALUES (?, ?)", (email, hashed_password))
            user_id = cursor.lastrowid
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (token, user_id, expires_at) VALUES (?, ?, ?);", (token, user_id, expires_at))

    response = RedirectResponse(url="/v2/app", status_code=303)
    response.set_cookie(key="session-id", value=token)

    return response


async def app(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="new/app.html",
        context={}
    )

async def login(request: Request):
    form_data = await request.form()
    print(form_data)
    email = form_data.get("email")
    password = form_data.get("password")

    return RedirectResponse(url="/v2", status_code=303)