import sqlite3


def get_user_with_password(conn: sqlite3.Connection, email: str) -> sqlite3.Row:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, email, hashed_password FROM user WHERE email = ?;", (email, ))
    db_user = cursor.fetchone()
    return db_user
