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
