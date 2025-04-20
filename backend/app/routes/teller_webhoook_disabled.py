
# File: app/routes/teller_webhook_disabled.py

from flask import Blueprint, jsonify, request

# Fallback blueprint if webhook is not configured
disabled_webhooks = Blueprint("webhooks_disabled", __name__)

@disabled_webhooks.route("/teller", methods=["POST", "GET", "OPTIONS"])
def disabled_teller_webhook():
    return jsonify({
        "status": "disabled",
        "message": "Webhook is not enabled. Please set TELLER_WEBHOOK_SECRET in your environment config."
    }), 501
