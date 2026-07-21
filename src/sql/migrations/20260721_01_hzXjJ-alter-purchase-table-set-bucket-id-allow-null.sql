-- Alter purchase table set bucket_id allow null 
-- depends: 20260131_02_hJBI0-fix-purchase-table-foreign-key

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
            bucket_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
            FOREIGN KEY(bucket_id) REFERENCES bucket(bucket_id) ON DELETE CASCADE
        );

INSERT INTO purchase_new (
    purchase_id, amount, currency, lotto_number, 
    purchased_at, timezone, created_at, updated_at, user_id, bucket_id
)
SELECT 
    purchase_id, amount, currency, lotto_number, 
    purchased_at, timezone, created_at, updated_at, user_id, bucket_id
FROM purchase;

DROP TABLE purchase;

-- 4. Rename the new table to the definitive name
ALTER TABLE purchase_new RENAME TO purchase;