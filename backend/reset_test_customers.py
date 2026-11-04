
from sqlalchemy import select

from backend.database import SessionLocal, User

EMAILS_TO_REMOVE = {
    "ikramsaniya@gmail.com",
    "saniyaikram.si@gmail.com",
    "saniyaikram.si@gmail.c",
    "ikramsaniya@gmail.c",
}

def reset_test_customers():
    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(User.email.in_(EMAILS_TO_REMOVE))
        ).all()

        if not users:
            print("No matching customer accounts found.")
            return

        for user in users:
            if user.role != "customer":
                print(f"Skipped non-customer account: {user.email}")
                continue

            if user.stripe_customer_id or user.stripe_subscription_id:
                print(f"Skipped Stripe-linked account: {user.email}")
                continue

            print(f"Removing test customer: {user.email}")
            db.delete(user)

        db.commit()
        print("Test customer reset completed.")


if __name__ == "__main__":
    reset_test_customers()
