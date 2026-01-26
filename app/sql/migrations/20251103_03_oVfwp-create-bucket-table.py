"""
Create bucket table
"""

from yoyo import step

__depends__ = {'20251103_02_f3p74-create-session-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS bucket(
            bucket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            is_daily INTEGER NOT NULL DEFAULT 0,
            month_start TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
        );""",
        "DROP TABLE IF EXISTS bucket;"),
    step("""CREATE UNIQUE INDEX IF NOT EXISTS idx_bucket_name_month_user
        ON bucket(user_id, month_start, name);""",
        "DROP INDEX IF EXISTS idx_bucket_name_month_user;")
]
