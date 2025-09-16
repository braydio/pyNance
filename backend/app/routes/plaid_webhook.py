"""Plaid webhooks endpoint for transactions and investments notifications."""

import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone

from app.config import PLAID_WEBHOOK_SECRET, logger
from app.extensions import db
from app.helpers.plaid_helpers import get_investment_transactions
from app.models import PlaidAccount, PlaidWebhookLog
from app.services.plaid_sync import sync_account_transactions
from app.sql import investments_logic
from flask import Blueprint, Request, jsonify, request

plaid_webhooks = Blueprint("plaid_webhooks", __name__)


def _verify_plaid_signature(req: Request) -> bool:
    """Validate the Plaid webhook signature using the shared secret.

    Args:
        req: Incoming Flask request containing the webhook payload.

    Returns:
        bool: ``True`` when the `Plaid-Signature` header matches the computed
        signature; otherwise ``False``.
    """

    signature_header = req.headers.get("Plaid-Signature")
    if not signature_header:
        logger.warning("Plaid webhook missing Plaid-Signature header.")
        return False

    components = {}
    try:
        for part in signature_header.split(","):
            if "=" not in part:
                continue
            key, value = (section.strip() for section in part.split("=", 1))
            components[key] = value
    except (IndexError, ValueError):
        logger.warning("Malformed Plaid-Signature header: %s", signature_header)
        return False

    timestamp = components.get("t")
    provided_signature = components.get("v1")

    if not timestamp or not provided_signature:
        logger.warning(
            "Plaid webhook signature header missing timestamp or signature component."
        )
        return False

    raw_body = req.get_data(as_text=True) or ""
    payload = f"{timestamp}.{raw_body}".encode("utf-8")
    computed_signature = hmac.new(
        PLAID_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload,
        digestmod=hashlib.sha256,
    ).hexdigest()
    is_valid = hmac.compare_digest(computed_signature, provided_signature)

    if not is_valid:
        logger.warning("Invalid Plaid webhook signature.")

    return is_valid


@plaid_webhooks.route("/plaid", methods=["POST"])
def handle_plaid_webhook():
    """Process Plaid webhook events after validating the request signature.

    Returns:
        Tuple[Response, int]: Flask response payload and HTTP status code.
    """

    if not PLAID_WEBHOOK_SECRET:
        logger.error("PLAID_WEBHOOK_SECRET is not configured; rejecting webhook.")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Plaid webhook secret not configured.",
                }
            ),
            500,
        )

    if not _verify_plaid_signature(request):
        return jsonify({"status": "invalid_signature"}), 400

    payload = request.get_json(silent=True) or {}
    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    item_id = payload.get("item_id")

    # Persist webhook log for observability
    try:
        log = PlaidWebhookLog(
            event_type=f"{webhook_type}:{webhook_code}",
            webhook_type=webhook_type,
            webhook_code=webhook_code,
            item_id=item_id,
            payload=payload,
            received_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Failed to store Plaid webhook log: {e}")

    # Banking transactions delta webhook
    if webhook_type == "TRANSACTIONS" and webhook_code in (
        "SYNC_UPDATES_AVAILABLE",
        "DEFAULT_UPDATE",
    ):
        if not item_id:
            logger.warning("Plaid webhook missing item_id; cannot dispatch sync")
            return jsonify({"status": "ignored"}), 200

        # Trigger sync for each account under this item
        accounts = PlaidAccount.query.filter_by(item_id=item_id).all()
        triggered = []
        for pa in accounts:
            try:
                res = sync_account_transactions(pa.account_id)
                triggered.append(res.get("account_id") or pa.account_id)
            except Exception as e:
                logger.error(f"Sync failed for account {pa.account_id}: {e}")

        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Investments transactions webhook
    if webhook_type == "INVESTMENTS_TRANSACTIONS" and webhook_code in (
        "DEFAULT_UPDATE",
        "HISTORICAL_UPDATE",
    ):
        if not item_id:
            logger.warning(
                "Investments webhook missing item_id; cannot dispatch refresh"
            )
            return jsonify({"status": "ignored"}), 200

        # Determine a safe fetch window (last 30 days)
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()

        accounts = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).all()
        triggered = []
        for pa in accounts:
            try:
                txs = get_investment_transactions(pa.access_token, start_date, end_date)
                count = investments_logic.upsert_investment_transactions(txs)
                triggered.append({"account_id": pa.account_id, "investment_txs": count})
            except Exception as e:
                logger.error(
                    f"Investments tx refresh failed for account {pa.account_id}: {e}"
                )
        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Holdings price/position changes webhook
    if webhook_type == "HOLDINGS" and webhook_code in ("DEFAULT_UPDATE",):
        if not item_id:
            logger.warning("Holdings webhook missing item_id; cannot dispatch refresh")
            return jsonify({"status": "ignored"}), 200

        accounts = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).all()
        triggered = []
        for pa in accounts:
            try:
                sums = investments_logic.upsert_investments_from_plaid(
                    pa.account.user_id if pa.account else None, pa.access_token
                )
                triggered.append({"account_id": pa.account_id, **sums})
            except Exception as e:
                logger.error(
                    f"Investments holdings refresh failed for account {pa.account_id}: {e}"
                )
        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Other webhook types
    return jsonify({"status": "ignored"}), 200
