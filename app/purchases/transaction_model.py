"""
DB model for purchases
"""
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, DECIMAL, Enum
from app.core.database import Base


class PaymentMethod(enum.Enum):
    CASH = 'cash'
    CARD = 'card'


class TransactionType(enum.Enum):
    """
    Enumeration to hold info about transaction types availabel in the app
    Purchase represents spending money and can either be cash or card.
    Topup represents adding money to the digital balance
    Withdraw represents removing money from the digital balance
    Withdraw also represents adding money to the cash balance
    """
    PURCHASE = 'purchase'
    TOPUP = 'topup'
    WITHDRAW = "withdraw"


# I buy something. it is a purchase
# it has a payment method
# cash or card


# I top up my account. it is a topup
# it has no payment method
# just goes straight to my 'spending account'
# it increases my digital balance and decreases my cash balance


# I withdraw money from my account. it is a withdrawal
# it has no payment method
# it decreases my digital balance and increases my cash balance


class Transaction(Base):
    """
    DB model for purchases
    id, created_at, updated_at are default columns
    items takes a string list of items
    price takes a float number to allow for currencies with decimal places
    currency takes a string to store the currency
    location takes a string to store the location of the purchase
    purchase time allows the user to change the time used for sorting. Users can enter data later in the day, and change the time later to reflect the actual time of purchase rather than the time of db creation
    If transaction type is purchase, payment method is required, cash or card
    """
    __tablename__ = 'expense_transactions'

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=True,
                        default=None, onupdate=datetime.utcnow)

    user_id = Column(Integer, nullable=False)
    items = Column(Text)
    price = Column(DECIMAL(precision=10, scale=2))
    currency = Column(String(256))
    location = Column(String(256))

    purchase_time = Column(DateTime(timezone=True),
                           nullable=False, default=datetime.utcnow)

    payment_method = Column(Enum(PaymentMethod), nullable=True)
    
    transaction_type = Column(Enum(TransactionType), nullable=False, default=TransactionType.PURCHASE)

    
