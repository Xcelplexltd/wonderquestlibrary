
import os
import getpass
from datetime import datetime, timezone

import stripe
from sqlalchemy import select
from backend.database import SessionLocal, User


def show_date(label, timestamp):
    if timestamp:
        value = datetime.fromtimestamp(
            timestamp, tz=timezone.utc
        ).strftime("%d %B %Y %H:%M UTC")
    else:
        value = "Not set"

    print(f"{label}: {value}")


def main():
    email = input(
        "Enter cancelled customer's email: "
    ).strip().lower()

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == email)
        )

        if user is None:
            print("Account not found")
            return

        print("Local status:", user.subscription_status)

        if not user.stripe_subscription_id:
            print("No linked Stripe subscription")
            return

        key = os.getenv("WQ_STRIPE_SECRET_KEY")

        if not key:
            key = getpass.getpass(
                "Enter Stripe TEST secret key: "
            )

        if not key.startswith("sk_test_"):
            print("A Stripe test-mode key is required.")
            return

        stripe.api_key = key

        sub = stripe.Subscription.retrieve(
            user.stripe_subscription_id
        )
        sub = sub.to_dict()

        print("Stripe status:", sub.get("status"))
        print(
            "Cancel at period end:",
            sub.get("cancel_at_period_end")
        )

        show_date(
            "Scheduled cancellation",
            sub.get("cancel_at")
        )
        show_date(
            "Cancellation recorded",
            sub.get("canceled_at")
        )
        show_date(
            "Subscription ended",
            sub.get("ended_at")
        )

        period_end = sub.get("current_period_end")

        if not period_end:
            items = (sub.get("items") or {}).get("data") or []
            if items:
                period_end = items[0].get(
                    "current_period_end"
                )

        show_date("Current period end", period_end)


if __name__ == "__main__":
    main()
