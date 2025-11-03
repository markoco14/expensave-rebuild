"""
Create bucket table
"""

from yoyo import step

__depends__ = {'20251103_02_f3p74-create-session-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS bucket(
            bucket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
        );""",
        "DROP TABLE IF EXISTS bucket;"),
    step("""CREATE UNIQUE INDEX IF NOT EXISTS idx_bucket_user_id_name
        ON bucket(user_id, name);""",
        "DROP INDEX IF EXISTS idx_bucket_user_id_name;")
]
