"""Plaid webhooks endpoint for transactions sync notifications."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.config import logger
from app.extensions import db
from app.models import PlaidAccount, PlaidWebhookLog
from app.services.plaid_sync import sync_account_transactions

plaid_webhooks = Blueprint("plaid_webhooks", __name__)


@plaid_webhooks.route("/plaid", methods=["POST"]) 
def handle_plaid_webhook():
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

    # Non-transaction webhook types
    return jsonify({"status": "ignored"}), 200

