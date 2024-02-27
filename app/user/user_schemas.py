from typing import Optional

from pydantic import BaseModel


class User(BaseModel):
    """User"""
    id: int
    email: str
    display_name: Optional[str] = None


class CreateUserHashed(BaseModel):
    email: str
    hashed_password: str