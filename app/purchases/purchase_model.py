"""
DB model for purchases
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, DECIMAL
from app.core.database import Base



class DBPurchase(Base):
    """
    DB model for purchases
    id, created_at, updated_at are default columns
    items takes a string list of items
    price takes a float number to allow for currencies with decimal places
    currency takes a string to store the currency
    location takes a string to store the location of the purchase
    purchase time allows the user to change the time used for sorting. Users can enter data later in the day, and change the time later to reflect the actual time of purchase rather than the time of db creation
    """
    __tablename__ = 'expense_purchases'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=True,
                        default=None, onupdate=datetime.utcnow)
    
    items = Column(Text)
    price = Column(DECIMAL(precision=10, scale=2))
    currency = Column(String(256))
    location = Column(String(256))
    purchase_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
