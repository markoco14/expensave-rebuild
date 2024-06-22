from typing import List
from decimal import Decimal

from sqlalchemy.orm import Session
from app.purchases.purchase_model import Transaction
from app.core import time_service

def calculate_day_total_spent(purchases: List[Transaction]) -> Decimal:
    return sum([purchase.price for purchase in purchases])

def get_user_today_purchases(current_user_id: int, db: Session):
    """ Returns a user's purchases for today"""
    start_of_day = time_service.get_utc_start_of_day(utc_offset=8)
    end_of_day = time_service.get_utc_end_of_day(utc_offset=8)
    
    db_purchases = db.query(Transaction).filter(
        Transaction.user_id == current_user_id,
        Transaction.purchase_time >= start_of_day,
        Transaction.purchase_time <= end_of_day
        ).order_by(Transaction.purchase_time.desc()).all()
    
    return db_purchases