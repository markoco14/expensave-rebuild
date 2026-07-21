"""
Fix purchase table foreign key
"""

from yoyo import step

__depends__ = {'20260131_01_M17IO-update-to-bucket-and-bucket-month-top-up'}

steps = [
    step("""
            CREATE TABLE purchase_new(
                purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                lotto_number TEXT,
                purchased_at TEXT NOT NULL,
                timezone TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT,
                user_id INTEGER NOT NULL,
                bucket_id INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
                FOREIGN KEY(bucket_id) REFERENCES bucket(bucket_id) ON DELETE CASCADE
            );
        """),

    step("""
        INSERT INTO purchase_new (
            purchase_id, amount, currency, lotto_number, purchased_at, 
            timezone, created_at, updated_at, user_id, bucket_id
        )
        SELECT 
            purchase_id, amount, currency, lotto_number, purchased_at, 
            timezone, created_at, updated_at, user_id, bucket_id 
        FROM purchase;
    """),
    
    step("ALTER TABLE purchase RENAME TO purchase_old_fkey;"),

    step("ALTER TABLE purchase_new RENAME TO purchase;")
    
]
