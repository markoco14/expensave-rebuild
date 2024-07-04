"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.purchases import purchase_service
from app.purchases.transaction_model import PaymentMethod, TransactionType

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

    lifetime_spent = purchase_service.get_user_lifetime_spent(
        db=db, current_user_id=current_user.id
    )

    total_cash_spend = 0
    total_card_spend = 0

    total_card_topups = 0 
    total_cash_topups = 0

    user_transactions = purchase_service.get_user_purchases(
        db=db,
        current_user_id=current_user.id
    )

    for transaction in user_transactions:
        if transaction.payment_method == PaymentMethod.CASH:
            total_cash_spend += transaction.price
        if transaction.payment_method == PaymentMethod.CARD:
            total_card_spend += transaction.price

        if transaction.transaction_type == TransactionType.TOPUP:
            total_card_topups += transaction.price
        if transaction.transaction_type == TransactionType.WITHDRAW:
            total_card_topups -= transaction.price
            total_cash_topups += transaction.price


    current_user.total_card_spend = total_card_spend
    current_user.total_cash_spend = total_cash_spend
    current_user.total_card_topups = total_card_topups
    current_user.total_cash_topups = total_cash_topups

    context = {
        "request": request,
        "user": current_user,
        "lifetime_spent": lifetime_spent,
        "cash_spend": total_cash_spend,
        "card_spend": total_card_spend,
    }

    return templates.TemplateResponse(
        name="/app/profile/profile-page.html",
        context=context
    )
