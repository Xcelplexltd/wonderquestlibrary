
import os
import stripe

from backend.database import SessionLocal, User

USER_ID = 3
SUBSCRIPTION_ID = "sub_1UVwciDzOwLWNTSz7hJPDlo7"
CUSTOMER_ID = "cus_VWwrLgRn033GEp"
PRICE_ID = "price_1UVrpUDzOwLWNTSz2BZHJgH8"

api_key = os.getenv("WQ_STRIPE_SECRET_KEY", "")

if not api_key.startswith("sk_test_"):
    raise SystemExit("STOP: Stripe sandbox API key is required.")

stripe.api_key = api_key

# Read the current, authoritative Stripe subscription.
subscription = stripe.Subscription.retrieve(SUBSCRIPTION_ID).to_dict()

metadata = subscription.get("metadata") or {}
items = (subscription.get("items") or {}).get("data") or []

checks = {
    "Stripe test mode": subscription.get("livemode") is False,
    "Correct subscription": subscription.get("id") == SUBSCRIPTION_ID,
    "Correct customer": subscription.get("customer") == CUSTOMER_ID,
    "Correct application": metadata.get("application") == "wonderquestlibrary",
    "Correct user": metadata.get("wq_user_id") == str(USER_ID),
    "Correct price": any(
        (item.get("price") or {}).get("id") == PRICE_ID
        for item in items
    ),
    "Subscription canceled": subscription.get("status") == "canceled",
}

for description, passed in checks.items():
    print(f"{description}: {'PASS' if passed else 'FAIL'}")

if not all(checks.values()):
    raise SystemExit("STOP: Stripe validation failed. Database unchanged.")

with SessionLocal() as db:
    user = db.get(User, USER_ID)

    if (
        user is None
        or user.role != "customer"
        or not user.is_active
        or user.stripe_customer_id != CUSTOMER_ID
        or user.stripe_subscription_id != SUBSCRIPTION_ID
        or user.subscription_status not in ("active", "canceled")
    ):
        raise SystemExit("STOP: Local customer validation failed. Database unchanged.")

    if user.subscription_status == "canceled":
        print("Already reconciled. No changes needed.")
    else:
        user.subscription_status = "canceled"
        db.commit()
        print("SUCCESS: Customer subscription status updated to canceled.")
