"""
Update to bucket and bucket_month_top_up
"""

from yoyo import step

__depends__ = {'20260125_01_Dxkun-fix-session-table-user-foreign-key'}

steps = [
    step("""
            CREATE TABLE bucket_new(
            bucket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_daily INTEGER NOT NULL CHECK (is_daily IN (0, 1)) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
            );
        """),
    
    step("""INSERT INTO bucket_new (name, is_daily, user_id) SELECT DISTINCT name, is_daily, user_id FROM bucket;"""),
    
    step("""CREATE TABLE purchase_backup AS SELECT * FROM purchase;"""),

    step("""
            UPDATE purchase
            SET bucket_id = (
                SELECT bn.bucket_id
                FROM bucket_new bn
                JOIN bucket bo ON bo.bucket_id = purchase.bucket_id
                WHERE bn.name = bo.name 
                AND bn.user_id = purchase.user_id
            );
        """),

    step("ALTER TABLE bucket RENAME TO bucket_old;"),

    step("ALTER TABLE bucket_new RENAME TO bucket;"),

    step("""
            CREATE TABLE bucket_month_top_up (
                top_up_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bucket_id INTEGER NOT NULL,
                month_start DATE NOT NULL,
                start_amount INTEGER NOT NULL,
                end_amount INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME,
                FOREIGN KEY(bucket_id) REFERENCES bucket(bucket_id) ON DELETE CASCADE,
                CONSTRAINT unique_bucket_month UNIQUE(bucket_id, month_start)
            );
        """),

    step("""
            INSERT INTO bucket_month_top_up (bucket_id, month_start, start_amount)
            SELECT b.bucket_id, bo.month_start, bo.amount
            FROM bucket_old bo
            JOIN bucket b ON bo.name = b.name AND bo.user_id = b.user_id;
        """)
]
