
import os
import smtplib
import ssl
from email.message import EmailMessage
import certifi

from itsdangerous import (
    URLSafeTimedSerializer,
    BadSignature,
    SignatureExpired,
)


def token_signer():
    secret = os.environ.get("WQ_VERIFY_SECRET")

    if not secret or len(secret) < 32:
        raise RuntimeError(
            "WQ_VERIFY_SECRET must contain at least 32 characters"
        )

    return URLSafeTimedSerializer(
        secret_key=secret,
        salt="wonderquest-email-verification-v1",
    )


def create_verification_token(user):
    return token_signer().dumps({
        "user_id": user.id,
        "email": user.email,
        "purpose": "verify-email",
    })


def read_verification_token(token):
    try:
        data = token_signer().loads(
            token,
            max_age=24 * 60 * 60,
        )
        if data.get("purpose") != "verify-email":
            return None
        return data
    except (BadSignature, SignatureExpired):
        return None


def send_verification_email(user, base_url):
    host = os.environ["WQ_SMTP_HOST"]
    port = int(os.environ.get("WQ_SMTP_PORT", "465"))
    username = os.environ["WQ_SMTP_USER"]
    password = os.environ["WQ_SMTP_PASSWORD"]
    sender = os.environ["WQ_EMAIL_FROM"]

    token = create_verification_token(user)
    link = (
        f"{base_url.rstrip('/')}/verify-email?token={token}"
    )

    message = EmailMessage()
    message["Subject"] = "Verify your Wonder Quest Library account"
    message["From"] = sender
    message["To"] = user.email

    message.set_content(
        "Welcome to Wonder Quest Library!\n\n"
        "Please verify your email address using this link:\n\n"
        f"{link}\n\n"
        "This link expires after 24 hours.\n\n"
        "If you did not create this account, "
        "you can ignore this email."
    )

    context = ssl.create_default_context(
    cafile=certifi.where()
)

    with smtplib.SMTP_SSL(
        host, port, context=context, timeout=15
    ) as server:
        server.login(username, password)
        server.send_message(message)

