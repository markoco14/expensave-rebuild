
import sqlite3
import time
import uuid

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app import cryptography
from app.models.user import User
from app.respository.session import store_session
from app.respository.user import get_user_with_password

templates = Jinja2Templates(directory="templates")

async def login(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    form_data = await request.form()

    previous_values = {}
    errors = {}

    email = form_data.get("email")
    previous_values["email"] = email
    if not email:
        errors["email"] =  "You need to enter your email."

    password = form_data.get("password")
    previous_values["password"] = password
    if not password:
        errors["password"] =  "You need to enter your password."

    with sqlite3.connect("db.sqlite3") as conn:
        db_user = get_user_with_password(conn=conn, email=email)

    if not db_user:
        errors["email"] =  "You need to enter your email."

    if db_user:
        if password and not cryptography.verify_password(plain_password=password, hashed_password=db_user["hashed_password"]):
            errors["password"] =  "You need to enter your password."

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="hv/auth/form.xml",
            context={
                "previous_values": previous_values,
                "errors": errors
                },
            headers={
                "Content-Type": content_type
                }
        )
    
    db_user = User(
        user_id=db_user["user_id"],
        email=db_user["email"],
        )
    
    token = str(uuid.uuid4())
    expires_at = int(time.time()) + (60 * 60 * 24 * 3)

    with sqlite3.connect("db.sqlite3") as conn:
        store_session(conn=conn, token=token, user_id=db_user.user_id, expires_at=expires_at)

    response = templates.TemplateResponse(
        request=request,
        name="hv/auth/form.xml",
        context={
            "saved": True,
            "previous_values": {},
            "errors": {}
            },
        headers={
            "Content-Type": content_type
            }
    )

    response.set_cookie(key="session-id", value=token)

    return response

async def logout(request: Request):
    accept_header = request.headers.get("accept", "")
    content_type = "application/vnd.hyperview+xml" if "hyperview" in accept_header else "text/xml"

    # if not request.state.user:
    #     return RedirectResponse(url="/signin", status_code=303)
        
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()        
        cursor.execute("DELETE FROM session where session_id = ?;", (request.state.user.session_id,))

    # response = RedirectResponse(url="/login", status_code=303)
    # response.delete_cookie("session-id")
    # return response
    response = templates.TemplateResponse(
        request=request,
        name="hv/auth/logout.xml",
        headers={
            "Content-Type": content_type
            }
    )

    response.delete_cookie(key="session-id")

    return response