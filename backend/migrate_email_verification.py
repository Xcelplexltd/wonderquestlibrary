
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / "wonderquest.db"

with sqlite3.connect(db_path) as connection:
    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(users)")
    }

    if "email_verified" not in columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN "
            "email_verified BOOLEAN NOT NULL DEFAULT 0"
        )
        print("Added email_verified column.")
    else:
        print("email_verified column already exists.")

    connection.execute(
        "UPDATE users SET email_verified = 1 "
        "WHERE role IN ('admin', 'test')"
    )

    connection.commit()

print("Email verification migration completed successfully.")
