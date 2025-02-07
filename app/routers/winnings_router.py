from datetime import datetime, time, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data import winnings
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
    context["time_periods"] = winnings.time_periods

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
    
    selected_period_winning_numbers = winnings.winning_numbers.get(str(selected_year), {}).get(selected_time_period, {})
    print(selected_period_winning_numbers)

    for db_purchase in db_purchases:
        if not db_purchase.receipt_lottery_number:
            continue
        # check special prize and grand prize
        print(f"Receipt number: {db_purchase.receipt_lottery_number}")

        # get only the digits
        extracted_receipt_digits = winnings.get_digits_from_receipt_id(db_purchase.receipt_lottery_number)
        print(f"Extracted digits: {extracted_receipt_digits}")
        
        is_special_prize_winner = winnings.check_all_digits_match(extracted_receipt_digits, selected_period_winning_numbers.get("special"))
        if is_special_prize_winner:
            winners.append(db_purchase)
            total_winnings += 10000000
            continue

        print(f"Special prize comparing {extracted_receipt_digits} with {selected_period_winning_numbers.get('special')}.. is winner?: {is_special_prize_winner}")
        # print(f"Match all digits of special prize: {is_special_prize_winner}")

        is_grand_prize_winner = winnings.check_all_digits_match(extracted_receipt_digits, selected_period_winning_numbers.get("grand"))
        if is_grand_prize_winner:
            winners.append(db_purchase)
            total_winnings += 2000000
            continue

        print(f"Grand prize comparing {extracted_receipt_digits} with {selected_period_winning_numbers.get('grand')}.. is  winner?: {is_grand_prize_winner}")
        # print(f"Match all digits of grand prize: {is_grand_prize_winner}")

        # check first prize winners
        first_prize_numbers = selected_period_winning_numbers.get("first")
        for index, first_prize_number in enumerate(first_prize_numbers):
            # check all digits match
            is_first_prize_first_winner = winnings.check_all_digits_match(extracted_receipt_digits, first_prize_number)
            if is_first_prize_first_winner:
                winners.append(db_purchase)
                total_winnings += 200000
                print(f"First prize all comparing {extracted_receipt_digits} with {first_prize_number}.. is  winner?: {is_first_prize_first_winner}")
                print(f"Winner found with amount: NT$ {total_winnings}")
                continue
            # print(f"Match all digits of first prize number {index + 1}: {is_first_prize_first_winner}")
            print(f"First prize all comparing {extracted_receipt_digits} with {first_prize_number}.. is  winner?: {is_first_prize_first_winner}")

            # check last 7 digits match
            recipt_last_seven_digits = winnings.get_last_seven_digits(extracted_receipt_digits)
            prize_last_sevent_digits = winnings.get_last_seven_digits(first_prize_number)
            is_last_seven_digits_match = winnings.check_all_digits_match(recipt_last_seven_digits, prize_last_sevent_digits)
            if is_last_seven_digits_match:
                winners.append(db_purchase)
                total_winnings += 40000
                continue
            print(f"First prize last 7 comparing {recipt_last_seven_digits} with {prize_last_sevent_digits}.. is  winner?: {is_last_seven_digits_match}")
            # print(f"Match last 7 digits of first prize number {index + 1}: {is_last_seven_digits_match}")

            # check last 6 digits match
            recipt_last_six_digits = winnings.get_last_six_digits(extracted_receipt_digits)
            prize_last_six_digits = winnings.get_last_six_digits(first_prize_number)
            is_last_six_digits_match = winnings.check_all_digits_match(recipt_last_six_digits, prize_last_six_digits)
            if is_last_six_digits_match:
                winners.append(db_purchase)
                total_winnings += 10000
                continue
            print(f"Match last 6 digits of first prize number {index + 1}: {is_last_six_digits_match}")

            # check last 5 digits match
            recipt_last_five_digits = winnings.get_last_five_digits(extracted_receipt_digits)
            prize_last_five_digits = winnings.get_last_five_digits(first_prize_number)
            is_last_five_digits_match = winnings.check_all_digits_match(recipt_last_five_digits, prize_last_five_digits)
            if is_last_five_digits_match:
                winners.append(db_purchase)
                total_winnings += 4000
                continue
            print(f"Match last 5 digits of first prize number {index + 1}: {is_last_five_digits_match}")

            # check last 4 digits match
            recipt_last_four_digits = winnings.get_last_four_digits(extracted_receipt_digits)
            prize_last_four_digits = winnings.get_last_four_digits(first_prize_number)
            is_last_four_digits_match = winnings.check_all_digits_match(recipt_last_four_digits, prize_last_four_digits)
            if is_last_four_digits_match:
                winners.append(db_purchase)
                total_winnings += 1000
                continue
            print(f"Match last 4 digits of first prize number {index + 1}: {is_last_four_digits_match}")

            # check last 3 digits match
            recipt_last_three_digits = winnings.get_last_three_digits(extracted_receipt_digits)
            prize_last_three_digits = winnings.get_last_three_digits(first_prize_number)
            is_last_three_digits_match = winnings.check_all_digits_match(recipt_last_three_digits, prize_last_three_digits)
            if is_last_three_digits_match:
                winners.append(db_purchase)
                total_winnings += 200
                continue
            print(f"Match last 3 digits of first prize number {index + 1}: {is_last_three_digits_match}")

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

