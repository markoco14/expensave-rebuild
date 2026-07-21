import sqlite3


def store_session(conn: sqlite3.Connection, token, user_id, expires_at) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO session (token, user_id, expires_at) VALUES (:token, :user_id, :expires_at);",
        {"token": token, "user_id": user_id, "expires_at": expires_at}
        )
