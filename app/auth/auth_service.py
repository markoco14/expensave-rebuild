""" Functions to handle Authentication concerns including passwords, sessions, and current user """

from datetime import datetime, timedelta
import secrets
from typing import Dict

from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.auth import session_service
from app.services import user_service

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """returns hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """returns True if password is correct, False if not"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token():
    return secrets.token_hex(16)


def generate_session_expiry():
    return datetime.now() + timedelta(days=3)

def get_session_cookie(cookies: Dict[str, str]):
    if not cookies.get("session-id"):
        return False
    
    return True

# def destroy_db_session(db: Session, session_token: str):
#     session_repository.destroy_session(db=db, session_id=session_token)

def is_session_expired(expiry: datetime):
    if expiry < datetime.now():
        return True
        

def get_session_data(db: Session, session_token: str):
    session_data = session_service.get_session_by_session_id(db=db, session_id=session_token)
    return session_data

def get_current_user(db: Session, cookies: Dict[str, str]):
    session_id = cookies.get("session-id") 
    if not session_id:
        return None
    
    session_data = get_session_data(db=db, session_token=session_id)
    if not session_data:
        return None
    
    db_user = user_service.get_user_by_id(db=db, user_id=session_data.user_id)
    if not db_user:
        return None
    
    return db_user
# def get_current_user(db: Session, user_id: int):
#     db_user = user_service.get_user_by_id(db=db, user_id=user_id)
#     return db_user
    