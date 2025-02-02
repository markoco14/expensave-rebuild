from datetime import datetime, timedelta, time
from decimal import Decimal
from typing import List

from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from app.core import time_service
from app.transaction.transaction_model import Transaction, TransactionType


def calculate_day_total_spent(purchases: List[Transaction]) -> Decimal:
    return sum([purchase.price for purchase in purchases if purchase.price])


def get_user_today_purchases(current_user_id: int, db: Session):
    """ Returns a user's purchases for today"""
    start_of_day = time_service.get_utc_start_of_day(utc_offset=8)
    end_of_day = time_service.get_utc_end_of_day(utc_offset=8)

    db_purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user_id,
        Transaction.purchase_time >= start_of_day,
        Transaction.purchase_time <= end_of_day,
        Transaction.transaction_type == TransactionType.PURCHASE,
    ).order_by(Transaction.purchase_time.desc()).all()

    return db_purchases

def get_user_purchases_by_date(current_user_id: int, selected_date: datetime, db: Session):
    """ Returns a user's purchases for today"""
    start_of_day = selected_date - timedelta(hours=8)
    end_of_day = datetime.combine(selected_date, time.max) - timedelta(hours=8)

    db_purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user_id,
        Transaction.purchase_time >= start_of_day,
        Transaction.purchase_time <= end_of_day,
        Transaction.transaction_type == TransactionType.PURCHASE,
    ).order_by(Transaction.purchase_time.desc()).all()

    return db_purchases


def get_user_purchases(
        current_user_id: int,
        db: Session
):
    db_purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user_id
    ).order_by(Transaction.purchase_time.desc()).all()

    return db_purchases


def get_user_lifetime_spent(current_user_id: int, db: Session):
    """returns the total amount of money a user has spent
    in the time they've used the app"""
    total_spending_query = text(
        """SELECT SUM(price) as total_spent
        FROM expense_transactions
        WHERE user_id = :user_id"""
    )

    result = db.execute(total_spending_query, {
                        "user_id": current_user_id}).fetchone().total_spent

    return result


def create_topup_transaction(
    db: Session,
    current_user_id: int,
    amount: Decimal,
    note: str = None
):
    """Create a topup transaction"""
    
    db_topup = Transaction(
        user_id=current_user_id,
        price=amount,
        currency="TWD",
        transaction_type=TransactionType.TOPUP,
        note=note
    )

    db.add(db_topup)
    db.commit()
    db.refresh(db_topup)
    return db_topup


def create_withdraw_transaction(
    db: Session,
    current_user_id: int,
    amount: Decimal,
    note: str = None
):
    """Create a topup transaction"""
    db_withdraw = Transaction(
        user_id=current_user_id,
        price=amount,
        currency="TWD",
        transaction_type=TransactionType.WITHDRAW,
        note=note
    )

    db.add(db_withdraw)
    db.commit()
    db.refresh(db_withdraw)
    return db_withdraw
