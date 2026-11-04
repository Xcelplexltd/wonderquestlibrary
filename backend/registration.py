
import hmac
import os
import re
import secrets
from html import escape
from email_validator import validate_email, EmailNotValidError
from backend.email_verification import (
    send_verification_email,
    read_verification_token,
)

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.auth import verify_password


from backend.auth import hash_password
from backend.page_templates import status_page
from backend.database import User, get_db
import logging
import threading
import time

router = APIRouter(tags=["Registration"])
logger = logging.getLogger(__name__)

RESEND_CSRF_COOKIE = "wq_resend_csrf"
RESEND_EMAIL_COOLDOWN = 300  # 5 minutes
RESEND_IP_COOLDOWN = 15      # 15 seconds

_resend_lock = threading.Lock()
_resend_email_requests = {}
_resend_ip_requests = {}

CSRF_COOKIE = "wq_registration_csrf"
COOKIE_SECURE = os.getenv(
    "WQ_COOKIE_SECURE", "false"
).lower() == "true"

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def registration_page(message="", status_code=200):
    notice = (
        f'<p style="color:#a94442">{escape(message)}</p>'
        if message else ""
    )

    
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Create Account - Wonder Quest Library</title>
      <link rel="stylesheet" href="/wq-account.css">
    </head>

    <body class="wq-page">

      <header class="wq-page-header">
        <a class="wq-brand" href="/home">
          Wonder Quest Library
        </a>

        <nav class="wq-page-nav">
          <a href="/home">Home</a>
          <a href="/stories.html">Stories</a>
          <a href="/games/">Games</a>
          <a href="/login">Sign In</a>
        </nav>
      </header>

      <main class="wq-main">
        <section class="wq-card">

          <h1>Create Your Account</h1>

          <p class="wq-muted">
            Join Wonder Quest Library and discover
            magical stories and educational games.
          </p>

          <p>
            Monthly membership:
            <strong>&pound;6.99</strong>
          </p>

          __NOTICE__

          <form class="wq-form"
                method="post"
                action="/register">

            <input type="hidden"
                   name="csrf_token"
                   value="__TOKEN__">

            <label for="email">Email address</label>
            <input id="email"
                   name="email"
                   type="email"
                   autocomplete="email"
                   maxlength="254"
                   required>

            <label for="password">
              Password (minimum 12 characters)
            </label>
            <input id="password"
                   name="password"
                   type="password"
                   autocomplete="new-password"
                   minlength="12"
                   required>

            <label for="confirm_password">
              Confirm password
            </label>
            <input id="confirm_password"
                   name="confirm_password"
                   type="password"
                   autocomplete="new-password"
                   required>

            <button class="wq-button" type="submit">
              Create Account
            </button>

          </form>

          <div class="wq-form-footer">
            <p>
              Already registered?
              <a href="/login">Sign In</a>
            </p>

            <p class="wq-muted">
              Payment is not collected during registration.
              You will verify your email before subscribing.
            </p>
          </div>

        </section>
      </main>

    </body>
    </html>
    """

    token = secrets.token_urlsafe(32)
    html = html.replace("__NOTICE__", notice)
    html = html.replace("__TOKEN__", token)

    response = HTMLResponse(html, status_code=status_code)
    response.set_cookie(
        CSRF_COOKIE,
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=600,
        path="/register",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page():
    return registration_page()


@router.post("/register", response_class=HTMLResponse)
def register_customer(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    origin = request.headers.get("origin")
    expected_origin = str(request.base_url).rstrip("/")

    if origin and origin != expected_origin:
        return HTMLResponse(
            "Invalid request origin", status_code=403
        )

    cookie_token = request.cookies.get(CSRF_COOKIE, "")

    if (
        not cookie_token
        or not hmac.compare_digest(cookie_token, csrf_token)
    ):
        return HTMLResponse(
            "Invalid registration token. Refresh the page.",
            status_code=403,
        )

    email = email.strip().lower()

    try:
        validated = validate_email(
            email,
            check_deliverability=False,
        )
        email = validated.normalized.lower()

        domain = email.rsplit("@", 1)[1]
        if len(domain.rsplit(".", 1)[-1]) < 2:
            raise ValueError("Invalid domain suffix")

    except (EmailNotValidError, ValueError):
        return registration_page(
            "Please enter a valid email address.", 400
        )

    if len(password) < 12 or len(password) > 128:
        return registration_page(
            "Password must be between 12 and 128 characters.",
            400,
        )

    if password != confirm_password:
        return registration_page(
            "Passwords do not match.", 400
        )

    existing = db.scalar(
        select(User).where(User.email == email)
    )

    if existing:
        return registration_page(
            "This email cannot be registered. "
            "Try signing in or contact support.",
            409,
        )

    customer = User(
        email=email,
        password_hash=hash_password(password),
        role="customer",
        is_active=False,
        email_verified=False,
        subscription_status="inactive",
    )

    db.add(customer)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return registration_page(
            "This email cannot be registered.", 409
        )
    try:
        send_verification_email(
            customer,
            str(request.base_url),
        )
    except Exception:
        return HTMLResponse(
            "<h2>Account created, but verification email "
            "could not be sent.</h2>"
            "<p>Your account remains inactive. "
            "Please contact support.</p>",
            status_code=503,
        )

    response = RedirectResponse(
        "/registration-success", status_code=303
    )
    response.delete_cookie(CSRF_COOKIE, path="/register")
    return response


@router.get("/registration-success", response_class=HTMLResponse)
def registration_success():
    return status_page(
        title="Please Verify Your Email",
        message=(
            "If your registration was successful, "
            "a verification email has been sent. "
            "Open the email and follow the verification "
            "link to activate your account. "
            "Once verified, you can sign in and "
            "continue to your membership."
        ),
        link_text="Return to Sign In",
        link_url="/login",
    )


@router.get("/verify-email", response_class=HTMLResponse)
def verify_email_page(token: str = ""):
    data = read_verification_token(token)

    if not data:
        return status_page(
            title="Verification Link Unavailable",
            message=(
                "This verification link is invalid or "
                "has expired. Please check the link "
                "in your email."
            ),
            link_text="Return to Sign In",
            link_url="/login",
            status_code=400,
        )

    safe_token = escape(token, quote=True)

    return HTMLResponse(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Verify Email - Wonder Quest Library</title>
      <link rel="stylesheet" href="/wq-account.css">
    </head>
    <body class="wq-page">

      <header class="wq-page-header">
        <a class="wq-brand" href="/home">
          Wonder Quest Library
        </a>
        <nav class="wq-page-nav">
          <a href="/home">Home</a>
          <a href="/stories.html">Stories</a>
          <a href="/games/">Games</a>
          <a href="/login">Sign In</a>
        </nav>
      </header>

      <main class="wq-main">
        <section class="wq-card">
          <h1>Verify Your Email</h1>

          <p>
            You're almost ready to explore
            Wonder Quest Library!
          </p>

          <p class="wq-muted">
            Select the button below to confirm
            your email address and activate
            your account.
          </p>

          <form method="post" action="/verify-email">
            <input type="hidden"
                   name="token"
                   value="{safe_token}">

            <button class="wq-button" type="submit">
              Verify My Email
            </button>
          </form>

        </section>
      </main>

    </body>
    </html>
    """)



@router.post("/verify-email", response_class=HTMLResponse)
def confirm_email_verification(
    request: Request,
    token: str = Form(...),
    db: Session = Depends(get_db),
):
    origin = request.headers.get("origin")

    if origin and origin != str(request.base_url).rstrip("/"):
        return status_page(
            title="Verification Unavailable",
            message="The verification request could not be accepted.",
            status_code=403,
        )

    data = read_verification_token(token)

    if not data:
        return status_page(
            title="Verification Link Unavailable",
            message="This verification link is invalid or has expired.",
            status_code=400,
        )

    user = db.get(User, data["user_id"])

    if (
        user is None
        or user.role != "customer"
        or user.email != data["email"]
    ):
        return status_page(
            title="Verification Failed",
            message="We could not verify this account.",
            status_code=400,
        )

    # Do not reactivate previously verified or revoked accounts.
    if user.email_verified:
        return status_page(
            title="Email Already Verified",
            message="This verification link has already been used.",
            link_text="Continue to Sign In",
            link_url="/login",
            status_code=400,
        )

    if user.is_active:
        return status_page(
            title="Verification Unavailable",
            message="Account verification could not be completed.",
            status_code=400,
        )

    # Activate the newly verified customer account.
    user.email_verified = True
    user.is_active = True

    db.commit()

    return status_page(
        title="Email Verified Successfully!",
        message=(
            "Your Wonder Quest Library account is now active. "
            "You can sign in and choose your monthly membership."
        ),
        link_text="Continue to Sign In",
        link_url="/login",
    )

@router.get("/resend-verification", response_class=HTMLResponse)
def resend_verification_page():
    html = """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Resend Verification - Wonder Quest Library</title>
      <link rel="stylesheet" href="/wq-account.css">
    </head>
    <body class="wq-page">
      <header class="wq-page-header">
        <a class="wq-brand" href="/home">
          Wonder Quest Library
        </a>
        <nav class="wq-page-nav">
          <a href="/home">Home</a>
          <a href="/stories.html">Stories</a>
          <a href="/games/">Games</a>
          <a href="/login">Sign In</a>
        </nav>
      </header>

      <main class="wq-main">
        <section class="wq-card">
          <h1>Resend Verification Email</h1>
          <p class="wq-muted">
            Didn't receive your verification email?
            Enter the email address used to register.
          </p>

          <form class="wq-form"
                method="post"
                action="/resend-verification">
            <input type="hidden"
                name="csrf_token"
                value="__TOKEN__">
            <label for="email">Email address</label>
            <input id="email"
                   name="email"
                   type="email"
                   autocomplete="email"
                   maxlength="254"
                   required>

            <button class="wq-button" type="submit">
              Resend Verification Email
            </button>
          </form>
        </section>
      </main>
    </body>
    </html>
    """

    token = secrets.token_urlsafe(32)
    html = html.replace("__TOKEN__", escape(token, quote=True))

    response = HTMLResponse(html)

    response.set_cookie(
        "wq_resend_csrf",
        token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=600,
        path="/resend-verification",
    )

    response.headers["Cache-Control"] = "no-store"

    return response

@router.post("/resend-verification", response_class=HTMLResponse)
def resend_verification_email(
    request: Request,
    email: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    origin = request.headers.get("origin")
    expected_origin = str(request.base_url).rstrip("/")

    if origin and origin != expected_origin:
        return status_page(
            title="Request Unavailable",
            message="The request could not be accepted.",
            status_code=403,
        )

    cookie_token = request.cookies.get(
        RESEND_CSRF_COOKIE, ""
    )

    if (
        not cookie_token
        or not hmac.compare_digest(cookie_token, csrf_token)
    ):
        return status_page(
            title="Request Unavailable",
            message="Please refresh the page and try again.",
            link_text="Try Again",
            link_url="/resend-verification",
            status_code=403,
        )

    confirmation = (
        "If an eligible account exists, a new verification "
        "email will be sent. Please check your inbox and "
        "spam folder."
    )

    # Use a generic response to avoid revealing
    # whether an email address has an account.
    def confirmation_page():
        response = status_page(
            title="Check Your Email",
            message=confirmation,
            link_text="Return to Sign In",
            link_url="/login",
        )
        response.delete_cookie(
            RESEND_CSRF_COOKIE,
            path="/resend-verification",
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    try:
        validated = validate_email(
            email.strip().lower(),
            check_deliverability=False,
        )
        normalized_email = validated.normalized.lower()
    except EmailNotValidError:
        return confirmation_page()

    client_ip = (
        request.client.host if request.client else "unknown"
    )
    now = time.monotonic()

    # Local development rate limiting.
    with _resend_lock:
        email_last = _resend_email_requests.get(
            normalized_email, -float("inf")
        )
        ip_last = _resend_ip_requests.get(
            client_ip, -float("inf")
        )

        if (
            now - email_last < RESEND_EMAIL_COOLDOWN
            or now - ip_last < RESEND_IP_COOLDOWN
        ):
            return confirmation_page()

        _resend_email_requests[normalized_email] = now
        _resend_ip_requests[client_ip] = now

        # Remove old entries to limit memory growth.
        for key, timestamp in list(
            _resend_email_requests.items()
        ):
            if now - timestamp > RESEND_EMAIL_COOLDOWN:
                del _resend_email_requests[key]

        for key, timestamp in list(
            _resend_ip_requests.items()
        ):
            if now - timestamp > RESEND_IP_COOLDOWN:
                del _resend_ip_requests[key]

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if (
        user is not None
        and user.role == "customer"
        and not user.email_verified
        and not user.is_active
    ):
        try:
            send_verification_email(
                user,
                str(request.base_url),
            )
        except Exception:
            logger.exception(
                "Verification email resend failed"
            )

    return confirmation_page()

