"""
Fix session table user foreign key
"""

from yoyo import step

__depends__ = {'20251105_01_U2aPD-create-purchase-table'}

steps = [
    step("""CREATE TABLE new_session (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(user_id)
            );
         """),
    step("""INSERT INTO new_session (
                session_id, token, user_id, expires_at
            ) SELECT session_id, token, user_id, expires_at   
            FROM session;
         """),
    step("DROP TABLE session;"),
    step("ALTER TABLE new_session RENAME TO session;")
]
