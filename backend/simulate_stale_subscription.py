
from backend.database import SessionLocal, User

USER_ID = 3
EXPECTED_SUBSCRIPTION = "sub_1UVwciDzOwLWNTSz7hJPDlo7"
EXPECTED_CUSTOMER = "cus_VWwrLgRn033GEp"

with SessionLocal() as db:
    user = db.get(User, USER_ID)

    if user is None:
        raise SystemExit("STOP: Customer not found.")

    if (
        user.role != "customer"
        or user.subscription_status != "canceled"
        or user.stripe_subscription_id != EXPECTED_SUBSCRIPTION
        or user.stripe_customer_id != EXPECTED_CUSTOMER
    ):
        raise SystemExit(
            "STOP: Customer details do not match. No changes made."
        )

    print("Customer verified:", user.id)
    print("Previous status:", user.subscription_status)

    user.subscription_status = "active"
    db.commit()

    print("Simulated stale status:", user.subscription_status)
    print("Only user ID 3 was updated.")
