"""
Create purchase table
"""

from yoyo import step

__depends__ = {'20251103_03_oVfwp-create-bucket-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS purchase(
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount NOT NULL,
            lotto_number TEXT,
            time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            user_id INTEGER NOT NULL,
            bucket_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
            FOREIGN KEY(bucket_id) REFERENCES bucket(bucket_id) ON DELETE CASCADE
        );""",
        "DROP TABLE IF EXISTS purchase;")
]
