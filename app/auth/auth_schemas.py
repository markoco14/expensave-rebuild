""" 
Authentication schemas for the application
includes schemas for user session
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel



class UserSession(BaseModel):
    """In App User Session"""
    id: int
    session_id: str
    user_id: int
    expires_at: datetime


class CreateUserSession(BaseModel):
    """Create user session"""
    session_id: str
    user_id: int
    expires_at: datetime