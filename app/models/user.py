from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    user_id: Optional[int] = None
    email: Optional[str] = None
    hashed_password: Optional[str] = None