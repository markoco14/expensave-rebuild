"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth import auth_service
from app.core.database import get_db
from app.core import links


router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse)
def get_user_profile(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    current_user = auth_service.get_current_user(
        db=db, cookies=request.cookies)

    if not current_user:
        context = {
            "request": request,
            "nav_links": links.unauthenticated_navlinks
        }
        return templates.TemplateResponse(
            name="/website/web-home.html",
            context=context
        )

    wallet_query = text("""
        SELECT digital_balance, cash_balance
        FROM expense_user_wallet
        WHERE user_id = :user_id
    """)
    wallet_data = db.execute(
        wallet_query, {"user_id": current_user.id}).fetchone()
    print(wallet_data)

    context = {
        "request": request,
    }
    if wallet_data:
        digital_balance = wallet_data.digital_balance
        cash_balance = wallet_data.cash_balance
        context["digital_balance"] = digital_balance
        context["cash_balance"] = cash_balance

    return templates.TemplateResponse(
        name="/app/profile/profile-page.html",
        context=context
    )
