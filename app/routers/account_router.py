"""User authentication routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from jinja2_fragments.fastapi import Jinja2Blocks

from app.auth import auth_service
from app.core.database import get_db
from app.core import links
from app.services import transaction_service
from app.purchases.transaction_model import PaymentMethod, TransactionType

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/account", response_class=HTMLResponse)
def get_user_account(
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

    current_user.lifetime_spending = transaction_service.get_user_lifetime_spent(
        db=db, current_user_id=current_user.id
    )

    total_cash_spend = 0
    total_card_spend = 0

    total_card_topups = 0
    total_cash_topups = 0

    user_transactions = transaction_service.get_user_purchases(
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
        "transactions": user_transactions,
    }

    if request.headers.get("HX-Request"):
        return block_templates.TemplateResponse(
            name="app/account/account-page.html",
            context=context,
            block_name="account_data"
        )

    return templates.TemplateResponse(
        name="/app/account/account-page.html",
        context=context
    )


@router.post("/deposit-to-card", response_class=HTMLResponse)
def deposit_to_card(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    deposit_amount: int = Form(...),
    deposit_note: Annotated[str, Form(...)] = None,
):
    """ Allow user to deposit money to their card. """
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
    db_topup_transaction = transaction_service.create_topup_transaction(
        db=db,
        current_user_id=current_user.id,
        amount=deposit_amount,
        note=deposit_note,
    )

    context = {
        "request": request,
    }

    return block_templates.TemplateResponse(
        name="app/account/account-page.html",
        context=context,
        block_name="deposit_form",
        headers={"HX-Trigger": "updateAccountData"}
    )


@router.post("/withdraw-to-cash", response_class=HTMLResponse)
def withdraw_to_cash(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    withdraw_amount: int = Form(...),
    withdraw_note: Annotated[str, Form(...)] = None,
):
    """ Allow user to deposit money to their card. """
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

    db_withdraw_transaction = transaction_service.create_withdraw_transaction(
        db=db,
        current_user_id=current_user.id,
        amount=withdraw_amount,
        note=withdraw_note,
    )

    context = {
        "request": request,
    }

    return block_templates.TemplateResponse(
        name="app/account/account-page.html",
        context=context,
        block_name="withdraw_form",
        headers={"HX-Trigger": "updateAccountData"}
    )


@router.get("/account/transactions", response_class=HTMLResponse)
def list_account_transactions(
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

    user_transactions = transaction_service.get_user_purchases(
        db=db,
        current_user_id=current_user.id
    )
    context = {
        "request": request,
        "transactions": user_transactions
    }
    return block_templates.TemplateResponse(
        name="app/account/account-page.html",
        context=context,
        block_name="history_list"
    )
