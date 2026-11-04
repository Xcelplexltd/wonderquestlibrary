
from backend.database import SessionLocal, User
from backend.email_verification import send_verification_email

TEST_EMAIL = "ikramsaniya@gmail.com"

with SessionLocal() as db:
    user = db.query(User).filter(
        User.email == TEST_EMAIL
    ).first()

    if user is None:
        print("Test account not found.")
    elif user.role != "customer":
        print("Account is not a customer.")
    elif user.email_verified:
        print("Email already verified.")
    else:
        send_verification_email(
            user,
            "http://127.0.0.1:8002"
        )
        print("Verification email submitted to Resend.")
