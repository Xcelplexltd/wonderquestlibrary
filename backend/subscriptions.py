
import os

import stripe
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.auth import verify_password

from backend.auth import get_session_user
from backend.database import User, get_db

router = APIRouter(tags=["Subscriptions"])

COOKIE_NAME = "wq_session"


def get_customer(request: Request, db: Session):
    token = request.cookies.get(COOKIE_NAME)
    user = get_session_user(db, token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Please sign in."
        )

    if (
        user.role != "customer"
        or not user.is_active
        or not user.email_verified
    ):
        raise HTTPException(
            status_code=403,
            detail="Customer account required."
        )

    return user


def stripe_settings():
    key = os.environ.get("WQ_STRIPE_SECRET_KEY", "")
    price_id = os.environ.get("WQ_STRIPE_PRICE_ID", "")

    if not key.startswith("sk_test_") or not price_id:
        raise HTTPException(
            status_code=503,
            detail="Stripe test mode is not configured."
        )

    stripe.api_key = key
    return price_id


@router.get("/subscribe", response_class=HTMLResponse)
def subscription_page(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_customer(request, db)

    if user.subscription_status in ("active", "trialing"):
        return HTMLResponse(
            "<h2>Your subscription is already active.</h2>"
            '<p><a href="/account">My Account</a></p>'
        )

    
    return HTMLResponse("""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport"
            content="width=device-width, initial-scale=1">
      <title>Membership - Wonder Quest Library</title>
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
          <a href="/account">My Account</a>
        </nav>
      </header>

      <main class="wq-main">
        <section class="wq-card" style="text-align:center">

          <h1>Wonder Quest Library</h1>
          <h2>Monthly Membership</h2>

          <h1>£6.99 / month</h1>

          <p>
            Enjoy our collection of illustrated
            educational stories and interactive games.
          </p>

          <p class="wq-muted">
            One monthly subscription for your household.
            Up to five simultaneous sessions per account.
          </p>

          <p class="wq-muted">
            No additional charges for individual
            stories or games.
          </p>

          <form method="post" action="/create-checkout">
            <button class="wq-button" type="submit">
              Continue to Secure Checkout
            </button>
          </form>

          <p style="margin-top:25px">
            <a href="/account">Back to My Account</a>
          </p>

        </section>
      </main>

    </body>
    </html>
    """)


@router.post("/create-checkout")
def create_checkout(
    request: Request,
    db: Session = Depends(get_db),
):
    # Require a same-origin browser form submission.
    origin = request.headers.get("origin", "")
    expected_origin = str(request.base_url).rstrip("/")

    if origin != expected_origin:
        raise HTTPException(
            status_code=403,
            detail="Invalid request origin."
        )

    user = get_customer(request, db)
    price_id = stripe_settings()

    if user.subscription_status in ("active", "trialing"):
        return RedirectResponse(
            "/account",
            status_code=303
        )

    try:
        # Reuse existing Stripe customer if one exists.
        if user.stripe_customer_id:
            customer_id = user.stripe_customer_id

            # Prevent a duplicate paid subscription.
            existing = stripe.Subscription.list(
                customer=customer_id,
                status="all",
                limit=100,
            )

            for sub in existing.auto_paging_iter():
                if sub.status in (
                    "active",
                    "trialing",
                    "past_due",
                    "unpaid",
                    "incomplete",
                    "paused",
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            "An existing subscription needs "
                            "to be reviewed before checkout."
                        ),
                    )
        else:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={
                    "wq_user_id": str(user.id),
                    "application": "wonderquestlibrary",
                },
                idempotency_key=f"wq-customer-{user.id}",
            )

            customer_id = customer.id
            user.stripe_customer_id = customer_id
            db.commit()

        # Checkout must match the authenticated user.
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            client_reference_id=str(user.id),
            subscription_data={
                "metadata": {
                    "wq_user_id": str(user.id),
                    "application": "wonderquestlibrary",
                }
            },
            success_url=(
                str(request.base_url).rstrip("/")
                + "/checkout-success"
            ),
            cancel_url=(
                str(request.base_url).rstrip("/")
                + "/subscribe"
            ),
        )

    except stripe.StripeError:
        raise HTTPException(
            status_code=502,
            detail="Stripe is temporarily unavailable."
        )

    return RedirectResponse(
        checkout.url,
        status_code=303,
    )


@router.get("/checkout-success", response_class=HTMLResponse)
def checkout_success():
    return HTMLResponse("""
    <!doctype html>
    <html lang="en">
    <head><meta charset="UTF-8"></head>
    <body style="font-family:Arial;text-align:center;
                 background:#f7f3e9;padding:60px 20px">
      <h1>Wonder Quest Library</h1>
      <h2>Checkout completed</h2>
      <p>
        Your subscription is being confirmed.
        Access will become available after
        payment verification.
      </p>
      <p><a href="/account">My Account</a></p>
    </body>
    </html>
    """)

@router.post("/manage-subscription")
def manage_subscription(
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    origin = request.headers.get("origin", "")
    expected_origin = str(request.base_url).rstrip("/")

    if origin != expected_origin:
        raise HTTPException(
            status_code=403,
            detail="Invalid request origin.",
        )

    user = get_customer(request, db)

    if not verify_password(password, user.password_hash):
        return RedirectResponse(
            "/confirm-subscription?error=invalid",
            status_code=303,
        )

    stripe_settings()

    if (
        user.subscription_status not in ("active", "trialing")
        or not user.stripe_customer_id
        or not user.stripe_subscription_id
    ):
        return RedirectResponse("/account", status_code=303)

    try:
        sub = stripe.Subscription.retrieve(
            user.stripe_subscription_id
        ).to_dict()

        if (
            sub["customer"] != user.stripe_customer_id
            or sub.get("livemode", False)
            or (sub.get("metadata") or {}).get("wq_user_id") != str(user.id)
            or (sub.get("metadata") or {}).get("application") != "wonderquestlibrary"
            or not any(
                item["price"]["id"] == os.environ["WQ_STRIPE_PRICE_ID"]
                for item in sub["items"]["data"]
            )
        ):
            raise HTTPException(
                status_code=403,
                detail="Subscription verification failed.",
            )

        portal = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=str(request.base_url).rstrip("/") + "/account",
        )

    except stripe.StripeError:
        raise HTTPException(
            status_code=502,
            detail="Subscription management is temporarily unavailable.",
        )

    return RedirectResponse(portal.url, status_code=303)
@router.get("/confirm-subscription", response_class=HTMLResponse)
def confirm_subscription(
    request: Request,
    error: str = "",
    db: Session = Depends(get_db),
):

    user = get_customer(request, db)

    if user.subscription_status not in ("active", "trialing"):
        return RedirectResponse("/account", status_code=303)
    error_message = ""

    if error == "invalid":
        error_message = """
        <p role="alert" style="
            color: #9A3434;
            background-color: #FFF1EE;
            border: 1px solid #E9C0B8;
            border-radius: 10px;
            padding: 12px 16px;
            margin: 18px 0;
        ">
            Incorrect password. Please try again.
        </p>
        """
    html = """
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1">
        <title>Confirm Parent Access - Wonder Quest Library</title>
        <link rel="stylesheet" href="/wq-account.css">
    </head>
    <body>
        <main class="wq-card">
            <h1>Confirm Parent Access</h1>
            <p>Please enter your account password
                to manage your subscription.</p>

            {error_message}

            <form method="post" action="/manage-subscription">
                <label for="password">Password</label>
                <input
                    type="password"
                    id="password"
                    name="password"
                    required
                    autocomplete="current-password"
                >
                <div class="wq-actions">
                    <button type="submit" class="wq-button">
                        Continue to Subscription Management
                    </button>
                </div>
            </form>

            <p><a href="/account">Back to My Account</a></p>
        </main>
    </body>
    </html>
    """
    return HTMLResponse(
        html.replace("{error_message}", error_message)
    )