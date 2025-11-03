
import sqlite3
import time
from types import SimpleNamespace
from fastapi import Request


def is_expired(expires_at):
        current_time = int(time.time())

        if current_time >= expires_at:
            return True
        
        return False
    

def is_user(request: Request):
    """Checks if user is a guest"""
    session_token = request.cookies.get("session-id", None)
    if not session_token: 
        request.state.user = None
        return
    
    with sqlite3.connect("db.sqlite3") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM session WHERE token = ?;", (session_token,))
        db_session = cursor.fetchone()

    if not db_session:
        request.state.user = None
        return
    
    if is_expired(expires_at=db_session[3]):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session WHERE token = ?;", (session_token))

        request.state.user = None
        return
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, email FROM user WHERE user_id = ?;", (db_session[2],))
        db_user = cursor.fetchone()

    if not db_user:
        request.state.user = None
        return
    
    request.state.user = SimpleNamespace(**db_user)
    return
