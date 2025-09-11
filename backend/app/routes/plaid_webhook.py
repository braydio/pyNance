"""Plaid webhooks endpoint for transactions and investments notifications."""

from datetime import datetime, timezone

from datetime import date, timedelta
from flask import Blueprint, jsonify, request

from app.config import logger
from app.extensions import db
from app.models import PlaidAccount, PlaidWebhookLog
from app.sql import investments_logic
from app.helpers.plaid_helpers import get_investment_transactions
from app.services.plaid_sync import sync_account_transactions
from flask import Blueprint, jsonify, request

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
            logger.warning("Investments webhook missing item_id; cannot dispatch refresh")
            return jsonify({"status": "ignored"}), 200

        # Determine a safe fetch window (last 30 days)
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()

        accounts = PlaidAccount.query.filter_by(item_id=item_id, product="investments").all()
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
    if webhook_type == "HOLDINGS" and webhook_code in (
        "DEFAULT_UPDATE",
    ):
        if not item_id:
            logger.warning("Holdings webhook missing item_id; cannot dispatch refresh")
            return jsonify({"status": "ignored"}), 200

        accounts = PlaidAccount.query.filter_by(item_id=item_id, product="investments").all()
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
