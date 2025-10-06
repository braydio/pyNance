# teller_webhook.py
import base64
import hashlib
import hmac

"""Teller webhook handlers for processing balance and transaction events."""

import json
import os
from datetime import datetime, timezone

from app.config import DIRECTORIES, FILES, logger
from app.extensions import db
from app.helpers.teller_helpers import load_tokens
from app.models import Account
from app.sql import account_logic
from flask import Blueprint, jsonify, request

TELLER_WEBHOOK_SECRET = os.getenv("TELLER_WEBHOOK_SECRET")
TELLER_DOT_CERT = FILES.get(
    "TELLER_DOT_CERT", DIRECTORIES["CERTS_DIR"] / "certificate.pem"
)
TELLER_DOT_KEY = FILES.get(
    "TELLER_DOT_KEY", DIRECTORIES["CERTS_DIR"] / "private_key.pem"
)
TELLER_API_BASE_URL = os.getenv("TELLER_API_BASE_URL", "https://api.teller.io")

webhooks = Blueprint("webhooks", __name__, url_prefix="/webhooks")
disabled_webhooks = Blueprint("webhooks_disabled", __name__)


@disabled_webhooks.route("/teller", methods=["POST", "GET", "OPTIONS"])
def disabled_teller_webhook():
    return (
        jsonify(
            {
                "status": "disabled",
                "message": "Webhook is not enabled. Please set TELLER_WEBHOOK_SECRET in your environment config.",
            }
        ),
        501,
    )


# Shared secret for signature verification (set in your Teller dashboard)


def verify_signature(request):
    signature = request.headers.get("Teller-Signature")
    if not signature:
        logger.warning("Missing Teller-Signature header.")
        return False
    if not TELLER_WEBHOOK_SECRET:
        logger.warning("TELLER_WEBHOOK_SECRET is not configured; rejecting webhook.")
        return False

    computed = hmac.new(
        TELLER_WEBHOOK_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256
    ).digest()
    computed_b64 = base64.b64encode(computed).decode()
    is_valid = hmac.compare_digest(computed_b64, signature)

    if not is_valid:
        logger.warning("Invalid Teller webhook signature.")
    return is_valid


@webhooks.route("/teller", methods=["POST"])
def teller_webhook():
    if not verify_signature(request):
        return jsonify({"status": "unauthorized"}), 401

    payload = request.get_json()
    logger.info(f"Received Teller webhook: {json.dumps(payload)}")

    event = payload.get("event")
    account_id = payload.get("data", {}).get("account_id")

    if not event or not account_id:
        logger.warning("Invalid webhook payload: missing event or account_id")
        return jsonify({"status": "invalid"}), 400

    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            logger.warning(f"Account {account_id} not found in DB")
            return jsonify({"status": "ok", "message": "Account not in system"}), 200

        tokens = load_tokens()
        access_token = next(
            (t["access_token"] for t in tokens if t["user_id"] == account.user_id), None
        )
        if not access_token:
            logger.warning(f"No token found for account {account_id}")
            return jsonify({"status": "ok", "message": "Token missing"}), 200

        logger.info(f"Handling webhook event: {event} for account {account_id}")

        if event in ["transaction.posted", "transaction.updated", "account.updated"]:
            updated = account_logic.refresh_data_for_teller_account(
                account,
                access_token,
                TELLER_DOT_CERT,
                TELLER_DOT_KEY,
                TELLER_API_BASE_URL,
            )
            if updated:
                account.last_refreshed = datetime.now(timezone.utc)
                db.session.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Error handling Teller webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
