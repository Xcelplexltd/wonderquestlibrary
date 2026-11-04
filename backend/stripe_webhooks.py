
import os
import logging

import stripe
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select

from backend.database import SessionLocal, User

router = APIRouter()
logger = logging.getLogger(__name__)

WATCHED_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}

def setting(name):
    value = os.getenv(name, "")
    if not value:
        raise HTTPException(
            status_code=503,
            detail="Webhook configuration unavailable",
        )
    return value


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    secret = setting("WQ_STRIPE_WEBHOOK_SECRET")
    api_key = setting("WQ_STRIPE_SECRET_KEY")
    price_id = setting("WQ_STRIPE_PRICE_ID")

    if not api_key.startswith("sk_test_"):
        raise HTTPException(503, "Test mode required")

    payload = await request.body()
    signature = request.headers.get(
        "stripe-signature", ""
    )

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe webhook",
        )

    event_type = event["type"]

    if event_type not in WATCHED_EVENTS:
        return {"received": True, "ignored": True}

    stripe.api_key = api_key

    try:
        # Fetch the current subscription state from Stripe.
        # This avoids applying stale webhook snapshots.
        subscription_id = event["data"]["object"]["id"]
        subscription = stripe.Subscription.retrieve(
            subscription_id
        )
        subscription = subscription.to_dict()

        if subscription.get("livemode", False):
            return {"received": True, "ignored": True}

        metadata = subscription.get("metadata") or {}

        if metadata.get("application") != "wonderquestlibrary":
            return {"received": True, "ignored": True}

        user_id = metadata.get("wq_user_id", "")
        if not user_id.isdigit():
            return {"received": True, "ignored": True}

        items = subscription["items"]["data"]
        matches_price = any(
            item["price"]["id"] == price_id
            for item in items
        )

        if not matches_price:
            return {"received": True, "ignored": True}

        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(
                    User.id == int(user_id)
                )
            )

            if (
                user is None
                or user.role != "customer"
                or user.stripe_customer_id
                   != subscription["customer"]
            ):
                return {"received": True, "ignored": True}

            # Never replace a different linked subscription
            # without a deliberate reconciliation process.
            if (
                user.stripe_subscription_id
                and user.stripe_subscription_id
                    != subscription_id
            ):
                return {"received": True, "ignored": True}

            user.stripe_subscription_id = subscription_id
            user.subscription_status = subscription["status"]
            db.commit()

        logger.info(
            "Wonder Quest subscription synchronized: %s",
            event_type,
        )
        return {"received": True}

    except stripe.StripeError:
        logger.exception("Stripe subscription synchronization failed")
        raise HTTPException(
            status_code=503,
            detail="Stripe synchronization unavailable",
        )
