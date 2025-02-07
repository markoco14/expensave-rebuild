from datetime import datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import winnings_service
from app.transaction.transaction_model import Transaction, TransactionType
from app.user.user_model import DBUser
from app.auth.auth_service import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/winnings/{selected_year}/{selected_time_period}", response_class=HTMLResponse)
def get_winnings_page(
    request: Request,
    selected_year: int,
    selected_time_period: str,
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
        "selected_year": selected_year,
        "selected_time_period": selected_time_period}
    
    # get the 2 months from the selected_time_period
    first_month = int(selected_time_period.split("-")[0])
    second_month = int(selected_time_period.split("-")[1])

    start_of_period = datetime(year=selected_year, month=first_month, day=1)

    if second_month == 12:
        end_date = datetime(year=selected_year + 1, month=1, day=1) - timedelta(days=1)
        end_of_period = datetime.combine(end_date, time.max)
    else:
        end_date = datetime(year=selected_year, month=second_month + 1, day=1) - timedelta(days=1)
        end_of_period = datetime.combine(end_date, time.max)

    context["start_of_period"] = start_of_period
    context["end_of_period"] = end_of_period
    context["time_periods"] = winnings_service.time_periods

    db_purchases = db.query(Transaction
                            ).filter(
                                Transaction.user_id == current_user.id,
                                Transaction.transaction_type == TransactionType.PURCHASE.value,
                                Transaction.purchase_time >= start_of_period,
                                Transaction.purchase_time <= end_of_period
                            ).order_by(
                                Transaction.purchase_time.asc()
                            ).all()
    
    if not db_purchases:
        context["purchases"] = {
            "first_month_purchases": [],
            "second_month_purchases": []
            }
    
        return templates.TemplateResponse(
            name="/winnings/index.html",
            context=context
        )
    
    # group by month
    first_month_purchases = []
    second_month_purchases = []

    winners = []
    total_winnings = 0

    selected_period_winning_numbers = winnings_service.winning_numbers.get(str(selected_year), {}).get(selected_time_period, {})
    
    if not selected_period_winning_numbers:
        context["purchases"] = {
            "first_month_purchases": first_month_purchases,
            "second_month_purchases": second_month_purchases
            }
        context["winners"] = winners
        context["total_winnings"] = total_winnings
        
        return templates.TemplateResponse(
            name="/winnings/index.html",
            context=context
        )
    
    for db_purchase in db_purchases:
        # skip if no lottery number recorded
        if not db_purchase.receipt_lottery_number:
            continue
        
        # get only the digits
        extracted_receipt_digits = winnings_service.get_digits_from_receipt_id(db_purchase.receipt_lottery_number)

        # check special prize
        is_special_prize_winner = winnings_service.check_all_digits_match(extracted_receipt_digits, selected_period_winning_numbers.get("special"))
        if is_special_prize_winner:
            winners.append(db_purchase)
            total_winnings += winnings_service.prize_amounts.get("special")
            continue

        # check grand prize
        is_grand_prize_winner = winnings_service.check_all_digits_match(extracted_receipt_digits, selected_period_winning_numbers.get("grand"))
        if is_grand_prize_winner:
            winners.append(db_purchase)
            total_winnings += winnings_service.prize_amounts.get("grand")
            continue

        # check first prize winners
        first_prize_numbers = selected_period_winning_numbers.get("first")
        for first_prize_number in first_prize_numbers:
            # check all digits match
            first_prize_number
            is_first_prize_first_winner = winnings_service.check_all_digits_match(extracted_receipt_digits, first_prize_number)
            if is_first_prize_first_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("eight")
                continue

            # check last 7 digits match
            recipt_last_seven_digits = winnings_service.get_last_seven_digits(extracted_receipt_digits)
            prize_last_seven_digits = winnings_service.get_last_seven_digits(first_prize_number)
            is_last_seven_digits_winner = winnings_service.check_all_digits_match(recipt_last_seven_digits, prize_last_seven_digits)
            if is_last_seven_digits_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("seven")
                continue

            # check last 6 digits match
            recipt_last_six_digits = winnings_service.get_last_six_digits(extracted_receipt_digits)
            prize_last_six_digits = winnings_service.get_last_six_digits(first_prize_number)
            is_last_six_digits_winner = winnings_service.check_all_digits_match(recipt_last_six_digits, prize_last_six_digits)
            if is_last_six_digits_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("six")
                continue

            # check last 5 digits match
            recipt_last_five_digits = winnings_service.get_last_five_digits(extracted_receipt_digits)
            prize_last_five_digits = winnings_service.get_last_five_digits(first_prize_number)
            is_last_five_digits_winner = winnings_service.check_all_digits_match(recipt_last_five_digits, prize_last_five_digits)
            if is_last_five_digits_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("five")
                continue

            # check last 4 digits match
            recipt_last_four_digits = winnings_service.get_last_four_digits(extracted_receipt_digits)
            prize_last_four_digits = winnings_service.get_last_four_digits(first_prize_number)
            is_last_four_digits_winner = winnings_service.check_all_digits_match(recipt_last_four_digits, prize_last_four_digits)
            if is_last_four_digits_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("four")
                continue

            # check last 3 digits match
            recipt_last_three_digits = winnings_service.get_last_three_digits(extracted_receipt_digits)
            prize_last_three_digits = winnings_service.get_last_three_digits(first_prize_number)
            is_last_three_digits_winner = winnings_service.check_all_digits_match(recipt_last_three_digits, prize_last_three_digits)
            if is_last_three_digits_winner:
                winners.append(db_purchase)
                total_winnings += winnings_service.prize_amounts.get("three")
                continue

        if db_purchase.purchase_time.month == first_month:
            first_month_purchases.append(db_purchase)
        else:
            second_month_purchases.append(db_purchase)
    
    context["purchases"] = {
        "first_month_purchases": first_month_purchases,
        "second_month_purchases": second_month_purchases
        }
    
    context["winners"] = winners
    context["total_winnings"] = total_winnings

    return templates.TemplateResponse(
        name="/winnings/index.html",
        context=context
    )

