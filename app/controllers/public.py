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


def home(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/index.html",
        context={}
    )


def signup(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/signup.html",
        context={}
    )


async def register(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
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

    response = RedirectResponse(url="/app", status_code=303)
    response.set_cookie(key="session-id", value=token)

    return response


async def login(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/login.html",
        context={}
    )


async def session(request: Request):
    if request.state.user:
        return RedirectResponse(url="/app", status_code=303)
    
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

    if not db_user:
        return "user does not exist"
    
    if not auth_service.verify_password(
            plain_password=password,
            hashed_password=db_user[2]
        ):
            return "wrong password"
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (token, user_id, expires_at) VALUES (?, ?, ?);", (token, db_user[0], expires_at))

    response = RedirectResponse(url="/app", status_code=303)
    response.set_cookie(key="session-id", value=token)

    return response


async def app(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="new/app.html",
        context={}
    )


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


async def buckets(request: Request, user_id: int):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    form_data = await request.form()

    bucket_name = form_data.get("bucket")

    if not bucket_name:
        return "You need a bucket name"
    
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO bucket (user_id, name) VALUES (?, ?);", (user_id, bucket_name))
        except Exception as e:
            return f"You already have a {bucket_name} bucket."
    
    return RedirectResponse(url="/me", status_code=303)