from datetime import datetime, date, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.transaction.transaction_model import Transaction, TransactionType
from app.user.user_model import DBUser
from app.auth.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/winnings/{time_period}", response_class=HTMLResponse)
def get_winnings_page(
    request: Request,
    time_period: str,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not current_user:
        context = {"request": request}
        return templates.TemplateResponse(
            name="/website/index.html",
            context=context
        )

    context = {
        "request": request,
        "user": current_user,
        "time_period": time_period}
    
    # get the 2 months from the time_period
    selected_year = 2024
    first_month = int(time_period.split("-")[0])
    second_month = int(time_period.split("-")[1])

    start_of_period = datetime(year=selected_year, month=first_month, day=1)

    if second_month == 12:
        end_date = datetime(year=selected_year + 1, month=1, day=1) - timedelta(days=1)
        end_of_period = datetime.combine(end_date, time.max)
    else:
        end_date = datetime(year=selected_year, month=second_month + 1, day=1) - timedelta(days=1)
        end_of_period = datetime.combine(end_date, time.max)

    db_purchases = db.query(Transaction
                            ).filter(
                                Transaction.user_id == current_user.id,
                                Transaction.transaction_type == TransactionType.PURCHASE.value,
                                Transaction.purchase_time >= start_of_period,
                                Transaction.purchase_time <= end_of_period
                            ).order_by(
                                Transaction.purchase_time.asc()
                            ).all()
    
    # group by month
    first_month_purchases = []
    second_month_purchases = []

    for db_purchase in db_purchases:
        if db_purchase.purchase_time.month == first_month:
            first_month_purchases.append(db_purchase)
        else:
            second_month_purchases.append(db_purchase)
    
    
    if not db_purchases:
        print("No purchases found")

    for purchase in db_purchases:
        print(f"{purchase.purchase_time}: {purchase.price}: {purchase.receipt_lottery_number}")

    context["purchases"] = {
        "first_month_purchases": first_month_purchases,
        "second_month_purchases": second_month_purchases
        }
    
    context["start_of_period"] = start_of_period
    context["end_of_period"] = end_of_period

    return templates.TemplateResponse(
        name="/winnings/index.html",
        context=context
    )

