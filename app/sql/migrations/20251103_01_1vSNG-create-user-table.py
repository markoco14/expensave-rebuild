"""
Create user table
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""CREATE TABLE IF NOT EXISTS user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT
        );""",
        "DROP TABLE IF EXISTS user;")
]
