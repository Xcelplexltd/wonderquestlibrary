

import hashlib
import secrets
from datetime import timedelta

from pwdlib import PasswordHash
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.database import User, UserSession, utc_now

password_hasher = PasswordHash.recommended()

MAX_SESSIONS = 5
SESSION_DURATION = timedelta(days=7)


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must have at least 12 characters")
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hasher.verify(password, stored_hash)



def authenticate_user(db: Session, email: str, password: str):
    email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    # Reject accounts that do not exist or have been disabled.
    if user is None or not user.is_active:
        return None

    # Customers must verify their email before login.
    # Administrator and test accounts are exempt.
    if user.role == "customer" and not user.email_verified:
        return None

    # Verify the submitted password.
    if not verify_password(password, user.password_hash):
        return None

    return user



def has_content_access(user: User) -> bool:
    if not user.is_active:
        return False

    if user.role in ("admin", "test"):
        return True

    return (
        user.role == "customer"
        and user.subscription_status == "active"
    )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(db: Session, user: User) -> str:
    if not user.is_active:
        raise PermissionError("Account is disabled")

    now = utc_now()

    # Mark expired sessions as revoked.
    expired = db.scalars(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at <= now,
        )
    ).all()

    for session in expired:
        session.revoked_at = now

    active_count = db.scalar(
        select(func.count(UserSession.id)).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )

    if active_count >= MAX_SESSIONS:
        db.commit()
        raise PermissionError(
            "Maximum of five active sessions reached"
        )

    token = secrets.token_urlsafe(32)

    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        created_at=now,
        expires_at=now + SESSION_DURATION,
    )

    db.add(session)
    db.commit()

    return token


def get_session_user(db: Session, token: str):
    if not token:
        return None

    now = utc_now()

    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
    )

    if session is None:
        return None

    user = db.get(User, session.user_id)

    if user is None or not user.is_active:
        return None

    return user


def revoke_session(db: Session, token: str):
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
        )
    )

    if session:
        session.revoked_at = utc_now()
        db.commit()


def revoke_all_sessions(db: Session, user_id: int):
    sessions = db.scalars(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
        )
    ).all()

    for session in sessions:
        session.revoked_at = utc_now()

    db.commit()


def require_admin(user: User):
    if not user.is_active or user.role != "admin":
        raise PermissionError("Administrator access required")

