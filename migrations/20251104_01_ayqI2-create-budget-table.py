"""
Create budget table
"""

from yoyo import step

__depends__ = {'20251103_03_oVfwp-create-bucket-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS budget(
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES user(user_id) 
        )""",
        "DROP TABLE IF EXISTS budget")
]
