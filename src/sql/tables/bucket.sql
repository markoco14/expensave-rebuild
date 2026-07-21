CREATE TABLE IF NOT EXISTS "bucket"(
            bucket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_daily INTEGER NOT NULL CHECK (is_daily IN (0, 1)) DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE
            );
