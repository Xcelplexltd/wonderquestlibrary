
import hashlib
import hmac
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.auth import get_session_user, revoke_all_sessions
from backend.database import User, UserSession, get_db, utc_now

router = APIRouter(prefix="/admin", tags=["Administration"])

COOKIE_NAME = "wq_session"


def admin_context(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    user = get_session_user(db, token)

    if user is None:
        raise HTTPException(status_code=401, detail="Please sign in")

    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required",
        )

    return user, token


def csrf_value(token: str, user_id: int, action: str):
    message = f"admin:{user_id}:{action}".encode("utf-8")
    return hmac.new(
        token.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()


def action_form(token, user_id, action, label, colour):
    csrf = csrf_value(token, user_id, action)

    return f"""
    <form method="post" action="/admin/users/{user_id}/action"
          style="display:inline-block;margin:3px">
      <input type="hidden" name="action" value="{action}">
      <input type="hidden" name="csrf_token" value="{csrf}">
      <button type="submit"
        style="background:{colour};color:white;border:0;
               border-radius:6px;padding:8px 12px;cursor:pointer">
        {label}
      </button>
    </form>
    """


@router.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        administrator, token = admin_context(request, db)
    except HTTPException as exc:
        if exc.status_code == 401:
            return RedirectResponse("/login", status_code=303)
        raise

    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    now = utc_now()
    rows = ""

    for user in users:
        active_sessions = db.scalar(
            select(func.count(UserSession.id)).where(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )

        status = "Active" if user.is_active else "Revoked"
        actions = ""

        if user.id != administrator.id:
            if user.is_active:
                actions += action_form(
                    token, user.id, "revoke",
                    "Revoke access", "#a94442",
                )
            else:
                actions += action_form(
                    token, user.id, "restore",
                    "Restore access", "#2e6f55",
                )

            actions += action_form(
                token, user.id, "sessions",
                "End sessions", "#526a83",
            )
        else:
            actions = "Current administrator"

        rows += f"""
        <tr>
          <td>{user.id}</td>
          <td>{escape(user.email)}</td>
          <td>{escape(user.role)}</td>
          <td>{status}</td>
          <td>{escape(user.subscription_status)}</td>
          <td>{active_sessions}</td>
          <td>{actions}</td>
        </tr>
        """

    return HTMLResponse(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Wonder Quest Administration</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background: #f7f3e9;
          margin: 0;
          padding: 28px;
          color: #243b30;
        }}
        main {{
          background: white;
          padding: 26px;
          border-radius: 14px;
          max-width: 1200px;
          margin: auto;
        }}
        h1 {{ color: #2e6f55; }}
        .table-wrap {{ overflow-x: auto; }}
        table {{
          width: 100%;
          border-collapse: collapse;
          min-width: 850px;
        }}
        th, td {{
          padding: 12px;
          border-bottom: 1px solid #ddd;
          text-align: left;
        }}
        th {{ background: #e9f0e9; }}
        a {{ color: #2e6f55; }}
      </style>
    </head>
    <body>
      <main>
        <h1>Wonder Quest Library</h1>
        <h2>Administrator Dashboard</h2>
        <p>Signed in as {escape(administrator.email)}</p>
        <p><a href="/account">Back to My Account</a></p>
        <h3>Registered Users ({len(users)})</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Email</th><th>Role</th>
                <th>Account</th><th>Subscription</th>
                <th>Active sessions</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      </main>
    </body>
    </html>
    """)


@router.post("/users/{user_id}/action")
def manage_user(
    user_id: int,
    request: Request,
    action: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    administrator, token = admin_context(request, db)

    if action not in ("revoke", "restore", "sessions"):
        raise HTTPException(status_code=400, detail="Invalid action")

    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        raise HTTPException(status_code=403, detail="Invalid origin")

    expected = csrf_value(token, user_id, action)

    if not hmac.compare_digest(csrf_token, expected):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == administrator.id:
        raise HTTPException(
            status_code=403,
            detail="Cannot modify your own administrator account",
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=403,
            detail="Cannot modify another administrator",
        )

    if action == "revoke":
        user.is_active = False
        revoke_all_sessions(db, user.id)

    elif action == "restore":
        user.is_active = True

    elif action == "sessions":
        revoke_all_sessions(db, user.id)

    db.commit()

    return RedirectResponse("/admin/", status_code=303)
