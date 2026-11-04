"""Wonder Quest Library: password recovery routes.

Install as backend/password_reset.py and include router in backend/main.py.
Required env: WQ_PASSWORD_RESET_SECRET, WQ_PUBLIC_BASE_URL,
WQ_EMAIL_FROM, WQ_RESEND_API_KEY (or WQ_SMTP_PASSWORD holding the Resend key).
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from email.message import EmailMessage
from html import escape
from urllib.parse import quote, urlsplit
from urllib.request import Request as URLRequest, urlopen
from urllib.error import HTTPError

from fastapi import APIRouter, BackgroundTasks, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.auth import hash_password
from backend.database import User, UserSession, get_db, utc_now

router = APIRouter(tags=["Password Recovery"])
logger = logging.getLogger(__name__)
RESET_SECONDS = 30 * 60
CSRF_SECONDS = 10 * 60
COOKIE_SECURE = os.getenv("WQ_COOKIE_SECURE", "false").lower() == "true"

# Suitable for a single-process local test. Add shared/persistent rate limiting
# at the application edge before a multi-worker/public deployment.
_rate_lock = threading.Lock()
_email_attempts = {}
_ip_attempts = {}


def _secret() -> bytes:
    value = os.environ.get("WQ_PASSWORD_RESET_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("Set WQ_PASSWORD_RESET_SECRET to a random 32+-character secret")
    return value.encode("utf-8")


def _public_url() -> str:
    value = os.environ["WQ_PUBLIC_BASE_URL"].rstrip("/")
    parsed = urlsplit(value)
    local_http = parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")
    if not (parsed.scheme == "https" or local_http) or not parsed.netloc:
        raise RuntimeError("WQ_PUBLIC_BASE_URL must be HTTPS (or HTTP localhost for testing)")
    if parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise RuntimeError("WQ_PUBLIC_BASE_URL must be an origin, not a path or credentialed URL")
    return value


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _password_fingerprint(user: User) -> str:
    return hashlib.sha256(user.password_hash.encode("utf-8")).hexdigest()


def _create_token(user: User) -> str:
    payload = {
        "uid": user.id,
        "exp": int(time.time()) + RESET_SECONDS,
        "pwd": _password_fingerprint(user),
        "nonce": secrets.token_hex(16),
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _b64encode(hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).digest())
    return encoded + "." + signature


def _validated_user(db: Session, token: str):
    if not token or len(token) > 2048 or token.count(".") != 1:
        return None
    try:
        encoded, signature = token.split(".", 1)
        expected = _b64encode(hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(_b64decode(encoded))
        if type(payload.get("uid")) is not int or type(payload.get("exp")) is not int:
            return None
        if not (int(time.time()) <= payload["exp"] <= int(time.time()) + RESET_SECONDS):
            return None
        user = db.get(User, payload["uid"])
        if user is None or not user.is_active:
            return None
        if user.role == "customer" and not user.email_verified:
            return None
        if not hmac.compare_digest(str(payload.get("pwd", "")), _password_fingerprint(user)):
            return None
        return user
    except (ValueError, TypeError, KeyError, AttributeError, UnicodeError, OverflowError):
        return None


def _rate_allowed(email: str, ip: str) -> bool:
    now = time.monotonic()
    with _rate_lock:
        for entries, ttl in ((_email_attempts, 300), (_ip_attempts, 60)):
            for key, last in list(entries.items()):
                if now - last > ttl:
                    del entries[key]
        if now - _email_attempts.get(email, -float("inf")) < 300:
            return False
        if now - _ip_attempts.get(ip, -float("inf")) < 15:
            return False
        _email_attempts[email] = now
        _ip_attempts[ip] = now
        return True


def _send_message(recipient: str, subject: str, body: str):
    """Deliver a recovery email using Resend's HTTPS API, not SMTP."""
    try:
        api_key = os.environ.get("WQ_RESEND_API_KEY") or os.environ["WQ_SMTP_PASSWORD"]
        payload = json.dumps({
            "from": os.environ["WQ_EMAIL_FROM"],
            "to": [recipient],
            "subject": subject,
            "text": body,
        }).encode("utf-8")
        request = URLRequest(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "WonderQuestLibrary/1.0",
            },
            method="POST",
        )
        # Default HTTPS handling verifies the server certificate.
        with urlopen(request, timeout=20) as response:
            if not 200 <= response.status < 300:
                logger.error("Wonder Quest recovery email rejected (HTTP %s)", response.status)
    except HTTPError as exc:
        try:
            details = json.loads(exc.read().decode("utf-8"))
        except (ValueError, UnicodeError):
            details = None

        if isinstance(details, dict):
            logger.error(
                "Resend error HTTP %s: name=%s; message=%s",
                exc.code,
                str(details.get("name", "unknown"))[:80],
                str(details.get("message", "No details"))[:250],
            )
        else:
            logger.error(
                "Resend error HTTP %s: non-JSON response; content-type=%s",
                exc.code,
                exc.headers.get("Content-Type", "unknown"),
            )
    except Exception:
        # Log the failure, but never log email bodies or reset tokens.
        logger.exception("Wonder Quest password recovery email could not be delivered")


def _send_reset_email(recipient: str, token: str):
    link = f"{_public_url()}/reset-password?token={quote(token, safe='')}"
    _send_message(
        recipient,
        "Reset your Wonder Quest Library password",
        "We received a request to reset your Wonder Quest Library password.\n\n"
        f"Open this link within 30 minutes:\n{link}\n\n"
        "If you did not request this, you can ignore this email.\n",
    )


def _send_confirmation_email(recipient: str):
    _send_message(
        recipient,
        "Your Wonder Quest Library password was changed",
        "Your Wonder Quest Library password has been reset. "
        "All previous sign-in sessions have been signed out.\n\n"
        "If this wasn't you, please contact the library administrator immediately.\n",
    )


def _html(title: str, content: str) -> HTMLResponse:
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="referrer" content="no-referrer">
  <title>{escape(title)} - Wonder Quest Library</title>
  <link rel="stylesheet" href="/wq-account.css">
</head>
<body class="wq-page">
  <main class="wq-main"><section class="wq-card">
    <h1>{escape(title)}</h1>{content}
  </section></main>
</body>
</html>"""
    response = HTMLResponse(body)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _forgot_form(csrf_token: str) -> HTMLResponse:
    return _html("Forgot Password", f"""
<p>Enter your registered email address to request a password reset link.</p>
<form class="wq-form" method="post" action="/forgot-password">
  <input type="hidden" name="csrf_token" value="{escape(csrf_token, quote=True)}">
  <label for="email">Email address</label>
  <input type="email" id="email" name="email" autocomplete="email" maxlength="254" required>
  <button class="wq-button" type="submit">Email Reset Link</button>
</form>
<p><a href="/login">Back to Sign In</a></p>""")


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page():
    csrf_token = secrets.token_urlsafe(32)
    response = _forgot_form(csrf_token)
    response.set_cookie(
        "wq_forgot_csrf", csrf_token, httponly=True,
        secure=COOKIE_SECURE, samesite="strict",
        path="/forgot-password", max_age=CSRF_SECONDS,
    )
    return response


@router.post("/forgot-password", response_class=HTMLResponse)
def request_password_reset(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    cookie = request.cookies.get("wq_forgot_csrf", "")
    if not cookie or not hmac.compare_digest(cookie, csrf_token):
        response = _html("Request Expired", '<p>Please reload the form and try again.</p><p><a href="/forgot-password">Try Again</a></p>')
        response.status_code = 403
        return response

    normalized = email.strip().lower()
    client_ip = request.client.host if request.client else "unknown"
    if len(normalized) <= 254 and _rate_allowed(normalized, client_ip):
        user = db.scalar(select(User).where(User.email == normalized))
        if user and user.is_active and (user.role != "customer" or user.email_verified):
            background_tasks.add_task(_send_reset_email, user.email, _create_token(user))

    response = _html(
        "Check Your Email",
        '<p>If this email is registered and eligible for recovery, '
        'we will send a password reset link. Please check your inbox.</p>'
        '<p><a href="/login">Back to Sign In</a></p>',
    )
    response.delete_cookie("wq_forgot_csrf", path="/forgot-password")
    return response


def _reset_form(token: str, error: str = "") -> HTMLResponse:
    warning = f'<p role="alert" style="color:#a02424">{escape(error)}</p>' if error else ""
    return _html("Create a New Password", f"""
<p>Choose a password containing at least 12 characters.</p>
{warning}
<form class="wq-form" method="post" action="/reset-password">
  <input type="hidden" name="token" value="{escape(token, quote=True)}">
  <label for="new_password">New password</label>
  <input id="new_password" name="new_password" type="password" minlength="12" autocomplete="new-password" required>
  <label for="confirm_password">Confirm new password</label>
  <input id="confirm_password" name="confirm_password" type="password" minlength="12" autocomplete="new-password" required>
  <button class="wq-button" type="submit">Reset Password</button>
</form>""")


def _invalid_link() -> HTMLResponse:
    response = _html(
        "Reset Link Unavailable",
        '<p>This password reset link is invalid, expired or has already been used.</p>'
        '<p><a href="/forgot-password">Request a New Link</a></p>',
    )
    response.status_code = 400
    return response


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(token: str = "", db: Session = Depends(get_db)):
    if _validated_user(db, token) is None:
        return _invalid_link()
    return _reset_form(token)


@router.post("/reset-password", response_class=HTMLResponse)
def complete_password_reset(
    background_tasks: BackgroundTasks,
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _validated_user(db, token)
    if user is None:
        return _invalid_link()
    if new_password != confirm_password:
        return _reset_form(token, "Passwords do not match.")
    if len(new_password) < 12:
        return _reset_form(token, "Password must contain at least 12 characters.")

    old_hash = user.password_hash
    new_hash = hash_password(new_password)
    # Conditional update prevents concurrent uses of the same token succeeding.
    result = db.execute(
        update(User)
        .where(User.id == user.id, User.password_hash == old_hash)
        .values(password_hash=new_hash)
    )
    if result.rowcount != 1:
        db.rollback()
        return _invalid_link()

    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=utc_now())
    )
    db.commit()
    background_tasks.add_task(_send_confirmation_email, user.email)

    response = _html(
        "Password Updated",
        '<p>Your password has been updated. Please sign in with your new password.</p>'
        '<p><a href="/login">Go to Sign In</a></p>',
    )
    response.delete_cookie("wq_session", path="/")
    return response
