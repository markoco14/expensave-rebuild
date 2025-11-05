"""
Create session table
"""

from yoyo import step

__depends__ = {'20251103_01_1vSNG-create-user-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS session (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(id)
        );""",
        "DROP TABLE IF EXISTS session;")
]
