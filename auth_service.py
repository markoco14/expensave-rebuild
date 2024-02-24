""" Functions to handle Authentication concerns including passwords, sessions, and current user """

from typing import Dict

def get_session_cookie(cookies: Dict[str, str]):
    if not cookies.get("session-id"):
        return False
    
    return True