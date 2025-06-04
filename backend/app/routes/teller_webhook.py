# teller_webhook.py
import hmac
import hashlib
import base64
import json
from flask import Blueprint, request, jsonify, current_app
from app.config import FILES, logger
from app.helpers.teller_helpers import load_tokens
from app.db_logic import account_logic
from app.extensions import db
from app.models import Account

TELLER_WEBHOOK_SECRET = FILES.get("TELLER_WEBHOOK_SECRET")

webhooks = Blueprint("webhooks", __name__, url_prefix="/webhooks")
disabled_webhooks = Blueprint("webhooks_disabled", __name__)


@disabled_webhooks.route("/teller", methods=["POST", "GET", "OPTIONS"])
def disabled_teller_webhook():
    return jsonify(
        {
            "status": "disabled",
            "message": "Webhook is not enabled. Please set TELLER_WEBHOOK_SECRET in your environment config.",
        }
    ), 501


# Shared secret for signature verification (set in your Teller dashboard)


def verify_signature(request):
    signature = request.headers.get("Teller-Signature")
    if not signature:
        logger.warning("Missing Teller-Signature header.")
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
                FILES["TELLER_DOT_CERT"],
                FILES["TELLER_DOT_KEY"],
                FILES["TELLER_API_BASE_URL"],
            )
            if updated:
                account.last_refreshed = datetime.utcnow()
                db.session.commit()

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Error handling Teller webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
