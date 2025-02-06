""" Functions to handle Authentication concerns including passwords, sessions, and current user """

from datetime import datetime, timedelta
import secrets
from typing import Annotated, Dict

from fastapi import Depends, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.auth import session_service
from app.auth.user_session_model import DBUserSession
from app.core.database import get_db
from app.user.user_model import DBUser

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


def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]):
    db_user = db.query(DBUser
                        ).join(
                            DBUserSession, DBUserSession.session_id == request.cookies.get("session-id")
                        ).filter(
                            DBUser.id == DBUserSession.user_id
                        ).first()

    return db_user