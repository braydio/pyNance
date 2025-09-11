"""Admin endpoints for managing Plaid webhooks on existing items."""

from flask import Blueprint, jsonify, request

from app.config import BACKEND_PUBLIC_URL, logger, plaid_client
from app.models import PlaidAccount

try:  # Plaid SDK request model (v9+)
    from plaid.model.item_webhook_update_request import ItemWebhookUpdateRequest
except Exception:  # pragma: no cover
    ItemWebhookUpdateRequest = None  # type: ignore


plaid_webhook_admin = Blueprint("plaid_webhook_admin", __name__)


@plaid_webhook_admin.route("/update", methods=["POST"])
def update_item_webhook():
    """Update the webhook URL for a Plaid item.

    Body may include one of:
      - item_id: Plaid item identifier
      - account_id: local external account_id (we will resolve to item)
      - webhook_url: optional explicit URL; otherwise derived from BACKEND_PUBLIC_URL
    """
    if ItemWebhookUpdateRequest is None:
        return (
            jsonify({
                "status": "error",
                "message": "Plaid SDK missing ItemWebhookUpdateRequest; upgrade SDK",
            }),
            500,
        )

    payload = request.get_json() or {}
    item_id = payload.get("item_id")
    account_id = payload.get("account_id")
    explicit_url = payload.get("webhook_url")

    webhook_url = explicit_url
    if not webhook_url and BACKEND_PUBLIC_URL:
        webhook_url = f"{str(BACKEND_PUBLIC_URL).rstrip('/')}/api/webhooks/plaid"

    if not webhook_url:
        return (
            jsonify({
                "status": "error",
                "message": "Missing webhook_url and BACKEND_PUBLIC_URL not set",
            }),
            400,
        )

    try:
        if not item_id and account_id:
            pa = PlaidAccount.query.filter_by(account_id=account_id).first()
            if not pa or not pa.item_id:
                return (
                    jsonify({
                        "status": "error",
                        "message": "Unable to resolve item_id from account_id",
                    }),
                    404,
                )
            item_id = pa.item_id

        if not item_id:
            return (
                jsonify({"status": "error", "message": "Missing item_id"}),
                400,
            )

        req = ItemWebhookUpdateRequest(item_id=item_id, webhook=webhook_url)
        resp = plaid_client.item_webhook_update(req)
        logger.info(f"Updated Plaid webhook for item {item_id} -> {webhook_url}")
        return jsonify({"status": "success", "item_id": item_id, "webhook": webhook_url}), 200

    except Exception as e:
        logger.error(f"Failed to update Plaid webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@plaid_webhook_admin.route("/update_all", methods=["POST"])
def update_all_items_webhook():
    """Update the webhook URL for all Plaid items in the database."""
    if ItemWebhookUpdateRequest is None:
        return (
            jsonify({
                "status": "error",
                "message": "Plaid SDK missing ItemWebhookUpdateRequest; upgrade SDK",
            }),
            500,
        )

    payload = request.get_json() or {}
    explicit_url = payload.get("webhook_url")
    webhook_url = explicit_url
    if not webhook_url and BACKEND_PUBLIC_URL:
        webhook_url = f"{str(BACKEND_PUBLIC_URL).rstrip('/')}/api/webhooks/plaid"
    if not webhook_url:
        return (
            jsonify({
                "status": "error",
                "message": "Missing webhook_url and BACKEND_PUBLIC_URL not set",
            }),
            400,
        )

    try:
        # Unique item_ids across all Plaid accounts
        item_ids = {pa.item_id for pa in PlaidAccount.query.filter(PlaidAccount.item_id.isnot(None)).all()}
        updated, errors = [], []
        for item_id in item_ids:
            try:
                req = ItemWebhookUpdateRequest(item_id=item_id, webhook=webhook_url)
                plaid_client.item_webhook_update(req)
                updated.append(item_id)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to update webhook for item {item_id}: {e}")
                errors.append({"item_id": item_id, "error": str(e)})
        return jsonify({"status": "success", "webhook": webhook_url, "updated": updated, "errors": errors}), 200
    except Exception as e:
        logger.error(f"Failed bulk webhook update: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
