CREATE TABLE IF NOT EXISTS "purchase"(
            purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL,
            lotto_number TEXT,
            purchased_at TEXT NOT NULL,
            timezone TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES user(user_id) ON DELETE CASCADE,
            FOREIGN KEY(category_id) REFERENCES "category"(category_id) ON DELETE CASCADE
        );
