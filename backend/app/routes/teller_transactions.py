"""REST endpoints for Teller token management and transaction sync flows."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List

from app.config import DIRECTORIES, FILES, logger
from app.extensions import db
from app.helpers.teller_helpers import load_tokens, save_tokens
from app.models import Account, Transaction
from app.sql import account_logic
from flask import Blueprint, jsonify, request

teller_cert_path = FILES.get(
    "TELLER_DOT_CERT", DIRECTORIES["CERTS_DIR"] / "certificate.pem"
)
teller_key_path = FILES.get(
    "TELLER_DOT_KEY", DIRECTORIES["CERTS_DIR"] / "private_key.pem"
)
TELLER_API_BASE_URL = os.getenv("TELLER_API_BASE_URL", "https://api.teller.io")

teller_transactions = Blueprint("teller_transactions", __name__)


def _build_token_map(tokens: Iterable[Dict[str, Any]]) -> Dict[str, str]:
    """Return a mapping of ``user_id`` to access token, excluding invalid rows."""

    mapping: Dict[str, str] = {}
    for token in tokens:
        user_id = token.get("user_id") if isinstance(token, dict) else None
        access_token = token.get("access_token") if isinstance(token, dict) else None
        if not user_id or not access_token:
            logger.warning("Ignoring invalid Teller token entry: %s", token)
            continue

        if user_id in mapping:
            logger.debug(
                "Overwriting existing access token for Teller user %s", user_id
            )
        mapping[user_id] = access_token

    return mapping


def _refresh_teller_account(
    account: Account, access_token: str, *, touch_last_refreshed: bool = False
) -> bool:
    """Refresh account data and optionally bump ``last_refreshed``."""

    updated = account_logic.refresh_data_for_teller_account(
        account,
        access_token,
        teller_cert_path,
        teller_key_path,
        TELLER_API_BASE_URL,
    )
    if updated and touch_last_refreshed:
        account.last_refreshed = datetime.now(timezone.utc)
    return bool(updated)


def _apply_transaction_updates(
    txn: Transaction, payload: Dict[str, Any]
) -> Dict[str, bool]:
    """Apply allowed transaction updates and return a map of changed fields."""

    changes: Dict[str, bool] = {}
    converters: Dict[str, Callable[[Any], Any]] = {
        "amount": lambda value: float(value),
        "date": lambda value: value,
        "description": lambda value: value,
        "category": lambda value: value,
        "merchant_name": lambda value: value,
        "merchant_type": lambda value: value,
    }

    for field, transform in converters.items():
        if field not in payload:
            continue

        try:
            new_value = transform(payload[field])
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning(
                "Failed to parse update for field %s on transaction %s: %s",
                field,
                txn.transaction_id,
                exc,
            )
            continue

        setattr(txn, field, new_value)
        changes[field] = True

    return changes


@teller_transactions.route("/save_access_token", methods=["POST"])
def save_teller_token():
    """Persist or update a Teller access token for the supplied user."""

    try:
        payload = request.get_json(silent=True) or {}
        access_token = payload.get("access_token")
        user_id = payload.get("user_id", "default-user")

        if not isinstance(access_token, str) or not access_token.strip():
            logger.warning("Missing access token in request body.")
            return (
                jsonify({"status": "error", "message": "Access token is required."}),
                400,
            )

        access_token = access_token.strip()
        logger.debug("Saving access token for user %s", user_id)
        tokens: List[Dict[str, Any]] = load_tokens()
        if not isinstance(tokens, list):
            logger.warning("Tokens file returned non-list payload; resetting store.")
            tokens = []

        updated = False
        for token in tokens:
            if isinstance(token, dict) and token.get("user_id") == user_id:
                token["access_token"] = access_token
                updated = True
                break

        if not updated:
            tokens.append({"user_id": user_id, "access_token": access_token})

        save_tokens(tokens)
        logger.info("Access token saved successfully for user %s", user_id)
        return jsonify({"status": "success"}), 200

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error saving Teller token: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@teller_transactions.route("/exchange_public_token", methods=["POST"])
def teller_exchange_public_token():
    """Inform callers that Teller tokens are provided directly without exchange."""

    logger.error(
        "Teller does not have an exchange process. Save response as linked token."
    )
    return (
        jsonify(
            {
                "error": "You are looking for the /teller_transactions/save_access_token route. This incorrect route is being depreciated.",
            }
        ),
        500,
    )


@teller_transactions.route("/refresh_accounts", methods=["POST"])
def teller_refresh_accounts():
    """Refresh Teller accounts and transactions using stored access tokens."""

    try:
        logger.debug("Refreshing Teller accounts from database.")
        token_map = _build_token_map(load_tokens())
        if not token_map:
            logger.warning("No Teller access tokens found; skipping refresh.")

        accounts = Account.query.all()
        updated_accounts: List[str] = []
        for account in accounts:
            access_token = token_map.get(account.user_id)
            if not access_token:
                logger.warning(
                    "No access token found for Teller user %s", account.user_id
                )
                continue

            logger.debug(
                "Refreshing Teller account %s (%s)",
                account.name,
                account.account_id,
            )
            if _refresh_teller_account(
                account, access_token, touch_last_refreshed=True
            ):
                updated_accounts.append(account.name)

        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Teller account data refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error refreshing Teller accounts: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@teller_transactions.route("/get_transactions", methods=["GET"])
def teller_get_transactions():
    """Return Teller transactions with optional pagination and filters."""

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 15))

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        category = request.args.get("category")

        start_date = (
            datetime.strptime(start_date_str, "%Y-%m-%d").date()
            if start_date_str
            else None
        )
        end_date = (
            datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
        )

        transactions_list, total = account_logic.get_paginated_transactions(
            page,
            page_size,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"transactions": transactions_list, "total": total},
                }
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error fetching Teller transactions: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@teller_transactions.route("/list_teller_accounts", methods=["GET"])
def get_accounts():
    """Return Teller accounts persisted in the database."""

    try:
        logger.debug("Fetching accounts from the database.")
        accounts = account_logic.get_accounts_from_db()
        logger.debug("Fetched %s accounts from DB.", len(accounts))
        return jsonify({"status": "success", "data": {"accounts": accounts}}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error fetching accounts from DB: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@teller_transactions.route("/refresh_balances", methods=["POST"])
def refresh_balances():
    """Refresh Teller account balances and update historical records."""

    try:
        token_map = _build_token_map(load_tokens())
        accounts = account_logic.get_accounts_from_db()
        updated_accounts: List[Dict[str, Any]] = []
        for acc in accounts:
            account = Account.query.filter_by(account_id=acc["account_id"]).first()
            if not account:
                logger.warning("Account %s not found in DB.", acc["account_id"])
                continue

            access_token = token_map.get(acc["user_id"])
            if not access_token:
                logger.warning(
                    "No access token found for Teller account %s", acc["account_id"]
                )
                continue

            if _refresh_teller_account(account, access_token):
                updated_accounts.append({"account_name": acc["name"]})

        db.session.commit()
        logger.debug("Balances refreshed for accounts: %s", updated_accounts)
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Balances refreshed",
                    "updated_accounts": updated_accounts,
                }
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error refreshing balances: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@teller_transactions.route("/update", methods=["PUT"])
def update_transaction():
    """Update a transaction's editable details."""

    try:
        data = request.get_json(silent=True) or {}
        transaction_id = data.get("transaction_id")
        if not transaction_id:
            return (
                jsonify({"status": "error", "message": "Missing transaction_id"}),
                400,
            )

        txn = Transaction.query.filter_by(transaction_id=transaction_id).first()
        if not txn:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404

        changed_fields = _apply_transaction_updates(txn, data)
        if not changed_fields:
            return jsonify({"status": "success", "message": "No changes applied"}), 200

        txn.user_modified = True
        existing_fields: Dict[str, bool] = {}
        if txn.user_modified_fields:
            try:
                existing_fields = json.loads(txn.user_modified_fields)
            except json.JSONDecodeError:  # pragma: no cover - defensive path
                logger.warning(
                    "Corrupt user_modified_fields JSON for transaction %s",
                    transaction_id,
                )
                existing_fields = {}
        for field in changed_fields:
            existing_fields[field] = True
        txn.user_modified_fields = json.dumps(existing_fields)

        db.session.commit()
        return jsonify({"status": "success"}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error updating transaction: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@teller_transactions.route("/delete_account", methods=["DELETE"])
def delete_teller_account():
    """Remove a Teller account and cascading data from the database."""

    try:
        data = request.get_json(silent=True) or {}
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        Account.query.filter_by(account_id=account_id).delete()
        db.session.commit()
        logger.info(
            "Deleted Teller account %s and related records via cascade.", account_id
        )
        return (
            jsonify(
                {"status": "success", "message": "Account and related records deleted"}
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Error deleting Teller account: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500
