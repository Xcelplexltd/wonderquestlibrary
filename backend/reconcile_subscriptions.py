
import argparse
import logging
import os
import sys

import stripe
from sqlalchemy import select

from backend.database import SessionLocal, User


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("wonderquest.reconciliation")


def reconcile(apply_changes=False):
    api_key = os.getenv("WQ_STRIPE_SECRET_KEY", "").strip()
    price_id = os.getenv("WQ_STRIPE_PRICE_ID", "").strip()

    # Sandbox-only until production configuration is reviewed.
    if not api_key.startswith("sk_test_"):
        raise RuntimeError("A Stripe test secret key is required.")

    if not price_id.startswith("price_"):
        raise RuntimeError("WQ_STRIPE_PRICE_ID is not configured.")

    stripe.api_key = api_key

    checked = 0
    updated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(
                User.role == "customer",
                User.stripe_subscription_id.is_not(None),
            )
        ).all()

        for user in users:
            checked += 1

            subscription_id = user.stripe_subscription_id
            customer_id = user.stripe_customer_id

            if not customer_id or not subscription_id.startswith("sub_"):
                skipped += 1
                logger.warning("Invalid linkage for user %s", user.id)
                continue

            try:
                subscription = stripe.Subscription.retrieve(
                    subscription_id
                ).to_dict()

                metadata = subscription.get("metadata") or {}
                items = (
                    (subscription.get("items") or {}).get("data") or []
                )

                price_matches = any(
                    (item.get("price") or {}).get("id") == price_id
                    for item in items
                )

                valid = all([
                    subscription.get("object") == "subscription",
                    subscription.get("livemode") is False,
                    subscription.get("id") == subscription_id,
                    subscription.get("customer") == customer_id,
                    metadata.get("application") == "wonderquestlibrary",
                    metadata.get("wq_user_id") == str(user.id),
                    price_matches,
                ])

                if not valid:
                    skipped += 1
                    logger.warning(
                        "Stripe identity validation failed for user %s",
                        user.id,
                    )
                    continue

                stripe_status = subscription.get("status")

                allowed_statuses = {
                    "active",
                    "trialing",
                    "past_due",
                    "unpaid",
                    "incomplete",
                    "incomplete_expired",
                    "canceled",
                    "paused",
                }

                if stripe_status not in allowed_statuses:
                    skipped += 1
                    logger.warning(
                        "Unrecognized Stripe status for user %s",
                        user.id,
                    )
                    continue

                if user.subscription_status == stripe_status:
                    logger.info(
                        "User %s already synchronized: %s",
                        user.id,
                        stripe_status,
                    )
                    continue

                logger.info(
                    "User %s: local=%s, Stripe=%s",
                    user.id,
                    user.subscription_status,
                    stripe_status,
                )

                if apply_changes:
                    user.subscription_status = stripe_status
                    db.commit()
                    updated += 1
                else:
                    logger.info(
                        "DRY RUN: no database change for user %s",
                        user.id,
                    )

            except stripe.StripeError:
                failed += 1
                db.rollback()
                logger.exception(
                    "Stripe lookup failed for user %s",
                    user.id,
                )

            except Exception:
                failed += 1
                db.rollback()
                logger.exception(
                    "Reconciliation failed for user %s",
                    user.id,
                )

    logger.info(
        "Finished: checked=%s updated=%s skipped=%s failed=%s",
        checked,
        updated,
        skipped,
        failed,
    )

    return failed == 0 and skipped == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write verified status changes to SQLite",
    )
    args = parser.parse_args()

    try:
        success = reconcile(apply_changes=args.apply)
        sys.exit(0 if success else 1)
    except Exception:
        logger.exception("Reconciliation could not start")
        sys.exit(1)
