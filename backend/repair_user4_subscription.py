
import os

import stripe
from sqlalchemy import select

from backend.database import SessionLocal, User

USER_ID = 4
EXPECTED_PRICE_ID = os.environ["WQ_STRIPE_PRICE_ID"]

stripe.api_key = os.environ["WQ_STRIPE_SECRET_KEY"]

with SessionLocal() as db:
    user = db.get(User, USER_ID)

    if (
        user is None
        or user.role != "customer"
        or not user.is_active
        or not user.email_verified
        or not user.stripe_customer_id
        or user.stripe_subscription_id
    ):
        raise RuntimeError("User 4 is not eligible for this repair")

    subscriptions = stripe.Subscription.list(
        customer=user.stripe_customer_id,
        status="all",
        limit=100,
    ).to_dict()["data"]

    matches = []

    for sub in subscriptions:
        metadata = sub.get("metadata") or {}

        price_matches = any(
            item["price"]["id"] == EXPECTED_PRICE_ID
            for item in sub["items"]["data"]
        )

        if (
            sub["status"] == "active"
            and not sub.get("livemode", False)
            and sub["customer"] == user.stripe_customer_id
            and metadata.get("wq_user_id") == str(USER_ID)
            and metadata.get("application") == "wonderquestlibrary"
            and price_matches
        ):
            matches.append(sub)

    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one matching active subscription; "
            f"found {len(matches)}. No changes made."
        )

    sub = matches[0]

    # Verify that no other local account already owns it.
    existing = db.scalar(
        select(User).where(
            User.stripe_subscription_id == sub["id"]
        )
    )

    if existing is not None:
        raise RuntimeError(
            "Subscription is already linked. No changes made."
        )

    print("Verified user:", USER_ID)
    print("Verified subscription status:", sub["status"])
    print("Subscription ownership and price: verified")

    confirmation = input(
        "Type REPAIR to update User 4 only: "
    )

    if confirmation != "REPAIR":
        print("Cancelled. No changes made.")
    else:
        user.stripe_subscription_id = sub["id"]
        user.subscription_status = sub["status"]

        db.commit()

        print("User 4 subscription repaired successfully.")
