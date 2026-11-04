
import getpass

from sqlalchemy import select

from backend.auth import hash_password
from backend.database import (
    User,
    SessionLocal,
    init_database,
)


ACCOUNTS = [
    ("wonderquest.admin@gmail.com", "admin"),
    ("getsetgoseries@gmail.com", "test"),
]


def create_initial_users():
    init_database()

    with SessionLocal() as db:
        for email, role in ACCOUNTS:
            existing = db.scalar(
                select(User).where(User.email == email)
            )

            if existing:
                print(f"Account already exists: {email}")
                continue

            print(f"\nCreating {role} account: {email}")

            password = getpass.getpass(
                "Enter password (minimum 12 characters): "
            )
            confirm = getpass.getpass("Confirm password: ")

            if password != confirm:
                print("Passwords do not match. Account skipped.")
                continue

            try:
                password_hash = hash_password(password)
            except ValueError as exc:
                print(f"Invalid password: {exc}")
                continue

            user = User(
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=True,
                subscription_status="inactive",
            )

            db.add(user)
            db.commit()
            print(f"Created {role} account successfully.")


if __name__ == "__main__":
    create_initial_users()
