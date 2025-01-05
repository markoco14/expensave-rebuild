"""
DB model for users
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, DECIMAL
from app.core.database import Base


class DBUser(Base):
    """
    DB model for users
    """
    __tablename__ = 'expense_users'

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True, default=None)
    last_name = Column(String(100), nullable=True, default=None)
    email = Column(String(length=256), unique=True)
    hashed_password = Column(String(length=256), nullable=True, default=None)
    is_superuser = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True, default=None)
    registered_at = Column(DateTime, nullable=True, default=None)
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=True,
                        default=None, onupdate=datetime.utcnow)
    
    digital_balance = Column(DECIMAL(precision=10, scale=2))
    cash_balance = Column(DECIMAL(precision=10, scale=2))
    feature_camera = Column(Boolean, default=False, nullable=False)
