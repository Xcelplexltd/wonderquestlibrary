
import os
from html import escape
from backend.password_reset import router as password_reset_router

from fastapi import FastAPI, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from backend.database import get_db, init_database
from backend.auth import (
    authenticate_user,
    create_session,
    get_session_user,
    revoke_session,
)

app = FastAPI(title="Wonder Quest Library API")
app.include_router(password_reset_router)
COOKIE_NAME = "wq_session"
COOKIE_SECURE = os.getenv("WQ_COOKIE_SECURE", "false").lower() == "true"


@app.on_event("startup")
def startup():
    init_database()


def current_user(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    return get_session_user(db, token)


@app.get("/")
def home():
    return {
        "application": "Wonder Quest Library",
        "status": "Backend running",
        "login": "/login",
    }


@app.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    db: Session = Depends(get_db),
):
    existing_token = request.cookies.get(COOKIE_NAME)
    existing_user = get_session_user(db, existing_token)

    if existing_user:
        return RedirectResponse(
            url="/account",
            status_code=303,
        )
    
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Sign In - Wonder Quest Library</title>
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
          <h1>Login!</h1>
          <p class="wq-muted">
            Sign in to continue your Wonder Quest adventure.
          </p>

          <form class="wq-form" method="post" action="/login">
            <label for="email">Email address</label>
            <input id="email" name="email" type="email"
                   autocomplete="email" required>

            <label for="password">Password</label>
            <input id="password" name="password"
                type="password"
                autocomplete="current-password" required>

            <p style="margin-top: 10px; text-align: right;">
                <a href="/forgot-password">Forgot Password?</a>
            </p>

            <button class="wq-button" type="submit">
            Sign In
            </button>
          </form>

          <div class="wq-form-footer">
            <p>New to Wonder Quest Library?</p>
            <a href="/register">Create an Account</a>
          </div>
        </section>
      </main>
      <footer class="wq-footer">
        <div class="wq-footer-inner">
            <strong>Wonder Quest Library</strong>

            <p>A little world of stories, games and discovery.</p>

            <p>
            Questions or enquiries? Contact us at
            <a href="mailto:admin@wonderquestlibrary.com">
                admin@wonderquestlibrary.com
            </a>
            </p>

            <small>
            &copy; 2026 Wonder Quest Library.
            All rights reserved.
            </small>
        </div>
        </footer>

    </body>
    </html>
    """




@app.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, email, password)

    if user is None:
        return HTMLResponse(
            "<h3>Invalid email or password.</h3>"
            '<a href="/login">Try again</a>',
            status_code=401,
        )

    # Check for an existing authenticated session.
    existing_token = request.cookies.get(COOKIE_NAME)
    existing_user = get_session_user(db, existing_token)

    # Reuse the session if it belongs to the same user.
    if existing_user and existing_user.id == user.id:
        return RedirectResponse(
            url="/account",
            status_code=303,
        )

    try:
        token = create_session(db, user)
    except PermissionError:
        return HTMLResponse(
            "<h3>Five active sessions already exist.</h3>"
            '<a href="/login">Back to login</a>',
            status_code=403,
        )

    # If switching accounts, invalidate the old session
    # after successfully creating the new one.
    if existing_token and existing_user:
        revoke_session(db, existing_token)

    response = RedirectResponse(
        url="/account",
        status_code=303,
    )

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/",
    )

    return response




@app.get("/account", response_class=HTMLResponse)
def account(
    request: Request,
    db: Session = Depends(get_db),
):
    user = current_user(request, db)

    if user is None:
        return RedirectResponse("/login", status_code=303)

    email = escape(user.email)
    role = escape(user.role.capitalize())

    status = escape(
        (user.subscription_status or "inactive")
        .replace("_", " ")
        .capitalize()
    )

    membership_section = ""

    if user.role == "customer":

        if user.subscription_status in ("active", "trialing"):
            membership_section = (
                '<p class="wq-muted">'
                'Your membership currently provides access '
                'to Stories and Games.</p>'
                '<div class="wq-actions">'
                '<form method="get" action="/confirm-subscription">'
                '<button type="submit" class="wq-button">'
                'Manage Subscription'
                '</button>'
                '</form>'
                '</div>'
            )
 
        # Check Stripe for a scheduled membership cancellation.
        if user.stripe_customer_id and user.stripe_subscription_id:
            try:
                import os
                import stripe
                from datetime import datetime, timezone

                stripe.api_key = os.environ["WQ_STRIPE_SECRET_KEY"]

                subscription = stripe.Subscription.retrieve(
                    user.stripe_subscription_id
                ).to_dict()

                metadata = subscription.get("metadata") or {}

                if (
                    subscription.get("customer") == user.stripe_customer_id
                    and not subscription.get("livemode", False)
                    and metadata.get("wq_user_id") == str(user.id)
                    and metadata.get("application") == "wonderquestlibrary"
                    and subscription.get("status") in ("active", "trialing")
                ):
                    cancel_at = subscription.get("cancel_at")

                    if not cancel_at and subscription.get(
                        "cancel_at_period_end"
                    ):
                        cancel_at = subscription.get("current_period_end")

                    if cancel_at:
                        end_date = datetime.fromtimestamp(
                            cancel_at, tz=timezone.utc
                        ).strftime("%d %B %Y")

                        membership_section = (
                            '<p class="wq-muted">'
                            '<strong>Cancellation scheduled</strong>'
                            '</p>'
                            '<p class="wq-muted">'
                            'Your membership will remain available until '
                            + escape(end_date) +
                            '. It will not renew automatically.'
                            '</p>'
                        ) + membership_section

            except (stripe.StripeError, KeyError, ValueError, TypeError):
                # Do not prevent account access if Stripe is unavailable.
                pass
            

        else:
            membership_section = (
                '<p class="wq-muted">'
                'A membership is required to access '
                'Stories and Games.</p>'
                '<div class="wq-actions">'
                '<a class="wq-button" href="/subscribe">'
                'View Membership - £6.99/month</a>'
                '</div>'
            )

    elif user.role == "admin":
        membership_section = (
            '<p class="wq-muted">'
            'Administrator access — no subscription required.'
            '</p>'
            '<div class="wq-actions">'
            '<a class="wq-button" href="/admin/">'
            'Administrator Dashboard</a>'
            '</div>'
        )

    elif user.role == "test":
        membership_section = (
            '<p class="wq-muted">'
            'Internal test account — no subscription required.'
            '</p>'
        )

    return HTMLResponse(f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>My Account - Wonder Quest Library</title>
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
          <a href="/account" aria-current="page">My Account</a>
        </nav>
      </header>

      <main class="wq-main">
        <section class="wq-card">
          <h1>My Account</h1>
          <p class="wq-muted">
            Welcome to your Wonder Quest Library.
          </p>

          <div class="wq-detail">
            <strong>Email address</strong>
            <p>{email}</p>
          </div>

          <div class="wq-detail">
            <strong>Account type</strong>
            <p>{role}</p>
          </div>

          <div class="wq-detail">
            <strong>Account status</strong>
            <p>Active</p>
          </div>

          <div class="wq-detail">
            <strong>Subscription status</strong>
            <p class="wq-status">{status}</p>
          </div>

          {membership_section}

          <div class="wq-actions">
            <form method="post" action="/logout">
              <button class="wq-button wq-button-secondary"
                      type="submit">
                Sign Out
              </button>
            </form>
          </div>

        </section>
      </main>

    </body>
    </html>
    """)



@app.post("/logout")
def logout(
    request: Request,
    db: Session = Depends(get_db),
):
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        return HTMLResponse(
            "Invalid request origin",
            status_code=403,
        )

    token = request.cookies.get(COOKIE_NAME)

    if token:
        revoke_session(db, token)

    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.get("/api/me")
def my_profile(
    request: Request,
    db: Session = Depends(get_db),
):
    user = current_user(request, db)

    if user is None:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "subscription_status": user.subscription_status,
    }


from backend.admin import router as admin_router
app.include_router(admin_router)

from backend.registration import router as registration_router
app.include_router(registration_router)

from backend.subscriptions import router as subscriptions_router
app.include_router(subscriptions_router)

from backend.stripe_webhooks import router as stripe_webhook_router
app.include_router(stripe_webhook_router)

from backend.content import router as content_router
app.include_router(content_router)