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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM session WHERE token = ?;", (session_token,))
        session = cursor.fetchone()

    if not session:
        request.state.user = None
        return
    
    session = SimpleNamespace(**session)
    
    if is_expired(expires_at=session.expires_at):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session WHERE session_id = ?;", (session.session_id, ))

        request.state.user = None
        return
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                        SELECT 
                        user.user_id, user.email, session.session_id 
                        FROM user 
                        JOIN session 
                        USING (user_id) 
                        WHERE user_id = ?;
                       """, (session.user_id,))
        db_user = cursor.fetchone()

    if not db_user:
        request.state.user = None
        return
    
    request.state.user = SimpleNamespace(**db_user)
    
    return

def is_purchase_owner(request: Request, purchase_id: int):
    request.state.purchase = None

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM purchase WHERE purchase_id = ?;", (purchase_id, ))
        row = cursor.fetchone()

    if row:
        request.state.purchase = SimpleNamespace(**row)

    return
    
