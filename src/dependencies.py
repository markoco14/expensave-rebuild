import sqlite3
import time
import logging
from types import SimpleNamespace

from fastapi import Request

logger = logging.getLogger(__name__)

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
    

def is_top_up_owner(request: Request, top_up_id: int):
    request.state.top_up = None

    if not request.state.user:
        return
    
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT btu.*
                           FROM bucket_month_top_up btu
                           JOIN bucket b USING(bucket_id)
                           WHERE btu.top_up_id = ?
                           AND b.user_id = ?;""",
                           (top_up_id, request.state.user.user_id))
            top_up = cursor.fetchone()
    except Exception as e:
        logger.error(f"unable to find top up for user:", e)
        return

    if top_up:
        request.state.top_up = SimpleNamespace(**top_up)
    
    return