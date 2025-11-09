import sqlite3
import time
import uuid

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import cryptography

templates = Jinja2Templates(directory="templates")


async def register(request: Request):
    if request.state.user:
        return RedirectResponse(url="/today", status_code=303)
    
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
        hashed_password = cryptography.get_password_hash(password)
        with sqlite3.connect("db.sqlite3") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user (email, hashed_password) VALUES (?, ?)", (email, hashed_password))
            user_id = cursor.lastrowid
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (token, user_id, expires_at) VALUES (?, ?, ?);", (token, user_id, expires_at))

    response = RedirectResponse(url="/today", status_code=303)
    response.set_cookie(key="session-id", value=token)

    return response


async def session(request: Request):
    if request.state.user:
        return RedirectResponse(url="/today", status_code=303)
    
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
    
    if not cryptography.verify_password(
            plain_password=password,
            hashed_password=db_user[2]
        ):
            return "wrong password"
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO session (token, user_id, expires_at) VALUES (?, ?, ?);", (token, db_user[0], expires_at))

    response = RedirectResponse(url="/today", status_code=303)
    response.set_cookie(key="session-id", value=token)

    return response


async def logout(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/signin", status_code=303)
        
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()        
        cursor.execute("DELETE FROM session where session_id = ?;", (request.state.user.session_id,))

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session-id")
    return response