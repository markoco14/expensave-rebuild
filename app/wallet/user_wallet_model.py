from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserWallet(Base):
    """
    Table to track available funds for users
    user_id tracks who the wallet belongs to
    digital_balance tracks the total digital balance, the balance available to card spending
    cash_balance tracks the total cash balance. This balance is taken from the digital balance every time a user makes a withdrawal
    """
    __tablename__ = 'expense_user_wallet'

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=True,
        default=None,
        onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('expense_users.id'))
    digital_balance = Column(Float, default=0.00)
    cash_balance = Column(Float, default=0.00)

    user = relationship('DBUser', back_populates='wallet')
