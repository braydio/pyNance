"""Account management and refresh routes."""

import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from app.config import logger
from app.extensions import db
from app.models import Account, PlaidItem, RecurringTransaction, Transaction
from app.sql.forecast_logic import update_account_history
from app.utils.finance_utils import (display_transaction_amount,
                                     normalize_account_balance)
from flask import Blueprint, jsonify, request

# Blueprint for generic accounts routes
accounts = Blueprint("accounts", __name__)


error_logger = logging.getLogger("pyNanceError")
if not error_logger.handlers:
    log_file = Path(__file__).resolve().parents[1] / "logs" / "account_sync_error.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file)
    error_logger.addHandler(handler)
error_logger.setLevel(logging.ERROR)


def resolve_account_by_any_id(identifier) -> Optional[Account]:
    """
    Resolve account by either numeric primary key or external account_id.

    Args:
        identifier: Either integer ID, string numeric ID, or external account_id

    Returns:
        Account object if found, None otherwise
    """
    # If identifier is numeric-like, try primary key first
    try:
        if isinstance(identifier, int) or (
            isinstance(identifier, str) and identifier.isdigit()
        ):
            acct = Account.query.get(int(identifier))
            if acct:
                return acct
    except Exception:
        pass

    # Fallback to external string account_id
    try:
        return Account.query.filter_by(account_id=str(identifier)).first()
    except Exception:
        return None


def _normalize_products(value) -> set[str]:
    """Return Plaid product identifiers from a persisted value."""

    if value is None:
        return set()
    if isinstance(value, str):
        return {item.strip() for item in value.split(",") if item.strip()}
    if isinstance(value, (set, list, tuple)):
        return {str(item).strip() for item in value if str(item).strip()}
    return {str(value).strip()}


def _plaid_products_for_account(account: Account) -> set[str]:
    """Return Plaid products enabled for the provided account."""

    products = set()
    plaid_rel = getattr(account, "plaid_account", None)
    if not plaid_rel:
        return products

    products.update(_normalize_products(getattr(plaid_rel, "product", None)))

    item_id = getattr(plaid_rel, "item_id", None)
    if item_id:
        items = PlaidItem.query.filter_by(item_id=item_id).all()
        for item in items:
            products.update(_normalize_products(getattr(item, "product", None)))

    if not products:
        products.add("transactions")
    return products


def _investment_date_range(start_date, end_date) -> tuple[str, str]:
    """Return ISO formatted date range for investments refresh logic."""

    def _coerce(value):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    return None
        return None

    end_dt = _coerce(end_date)
    start_dt = _coerce(start_date)

    if not end_dt:
        end_dt = datetime.now(timezone.utc).date()
    if not start_dt:
        start_dt = end_dt - timedelta(days=30)

    return start_dt.isoformat(), end_dt.isoformat()


def _refresh_plaid_investments(
    account: Account, access_token: str, start_date=None, end_date=None
) -> bool:
    """Refresh Plaid investments data for an account."""

    from app.helpers.plaid_helpers import get_investment_transactions
    from app.sql import investments_logic

    start_iso, end_iso = _investment_date_range(start_date, end_date)
    summary = investments_logic.upsert_investments_from_plaid(
        account.user_id, access_token
    )
    transactions = investments_logic.upsert_investment_transactions(
        get_investment_transactions(access_token, start_iso, end_iso)
    )

    securities_count = int(summary.get("securities", 0) or 0)
    holdings_count = int(summary.get("holdings", 0) or 0)
    tx_count = int(transactions or 0)

    return bool(securities_count or holdings_count or tx_count)


@accounts.route("/refresh_accounts", methods=["POST"])
def refresh_all_accounts():
    """Refresh all linked accounts for their enabled products."""
    try:
        from app.sql import account_logic

        data = request.get_json() or {}
        account_ids = data.get("account_ids") or []
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        logger.debug("Starting refresh of all linked accounts.")

        query = Account.query
        if account_ids:
            query = query.filter(Account.account_id.in_(account_ids))
        accounts = query.all()
        updated_accounts = []
        refreshed_counts: dict[str, int] = {}
        error_map: dict[tuple[str, str, str], dict] = {}

        for account in accounts:
            if account.link_type == "Plaid":
                access_token = None
                if account.plaid_account:
                    access_token = account.plaid_account.access_token
                if not access_token:
                    logger.warning(f"No Plaid token for {account.account_id}")
                    continue

                logger.debug(f"Refreshing Plaid account {account.account_id}")
                inst = account.institution_name or "Unknown"
                products = _plaid_products_for_account(account)
                account_updated = False

                for product_name in products:
                    if product_name == "transactions":
                        updated, err = account_logic.refresh_data_for_plaid_account(
                            access_token,
                            account.account_id,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        if err:
                            key = (
                                inst,
                                err.get("plaid_error_code"),
                                err.get("plaid_error_message"),
                            )
                            if key not in error_map:
                                error_map[key] = {
                                    "institution_name": inst,
                                    "account_ids": [account.account_id],
                                    "account_names": [account.name],
                                    "plaid_error_code": err.get("plaid_error_code"),
                                    "plaid_error_message": err.get(
                                        "plaid_error_message"
                                    ),
                                }

                                if err.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED":
                                    error_map[key]["requires_reauth"] = True
                                    error_map[key][
                                        "update_link_token_endpoint"
                                    ] = "/api/plaid/transactions/generate_update_link_token"
                                    error_map[key]["affected_account_ids"] = [
                                        account.account_id
                                    ]
                            else:
                                error_map[key]["account_ids"].append(account.account_id)
                                error_map[key]["account_names"].append(account.name)

                                if err.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED":
                                    affected_ids = set(
                                        error_map[key].get("affected_account_ids", [])
                                    )
                                    affected_ids.add(account.account_id)
                                    error_map[key]["affected_account_ids"] = list(
                                        affected_ids
                                    )

                            if err.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED":
                                logger.warning(
                                    f"Plaid re-auth required: Institution: {inst}, Account: {account.name}, "
                                    f"Error: {err.get('plaid_error_message')}. User must re-auth via Link update mode. "
                                    f"Call POST /api/plaid/transactions/generate_update_link_token with account_id."
                                )
                            else:
                                error_logger.error(
                                    f"Plaid error on refresh: Institution: {inst}, Accounts: {account.name}, "
                                    f"Error Code: {err.get('plaid_error_code')}, Message: {err.get('plaid_error_message')}"
                                )
                        else:
                            account_updated = account_updated or updated
                            if updated and account.plaid_account:
                                account.plaid_account.last_refreshed = datetime.now(
                                    timezone.utc
                                )
                    elif product_name == "investments":
                        try:
                            investments_updated = _refresh_plaid_investments(
                                account,
                                access_token,
                                start_date=start_date,
                                end_date=end_date,
                            )
                            account_updated = account_updated or investments_updated
                            if account.plaid_account:
                                account.plaid_account.last_refreshed = datetime.now(
                                    timezone.utc
                                )
                        except Exception as exc:
                            error_logger.error(
                                "Plaid investments refresh failed for account %s: %s",
                                account.account_id,
                                exc,
                                exc_info=True,
                            )
                    else:
                        logger.info(
                            "Skipping unsupported Plaid product %s for account %s",
                            product_name,
                            account.account_id,
                        )

                if account_updated:
                    updated_accounts.append(account.name)
                    refreshed_counts[inst] = refreshed_counts.get(inst, 0) + 1

            else:
                logger.info(
                    f"Skipping account {account.account_id} with unknown link_type {account.link_type}"
                )

        # Log aggregated error summary for operators
        if error_map:
            logger.info("=== Account Refresh Error Summary ===")
            for key, error_info in error_map.items():
                institution, error_code, error_message = key
                affected_count = len(error_info["account_ids"])
                account_names = ", ".join(
                    error_info["account_names"][:3]
                )  # Show first 3 names
                if len(error_info["account_names"]) > 3:
                    account_names += f" and {len(error_info['account_names']) - 3} more"

                log_level = (
                    "WARNING" if error_code == "ITEM_LOGIN_REQUIRED" else "ERROR"
                )
                remediation = ""
                if error_code == "ITEM_LOGIN_REQUIRED":
                    remediation = " | Remediation: User must re-auth via Link update mode. Call POST /api/plaid/transactions/generate_update_link_token with account_id."

                logger.info(
                    f"[{log_level}] {institution}: {error_code} - {error_message} | "
                    f"Affected accounts: {affected_count} ({account_names}){remediation}"
                )
            logger.info("=== End Error Summary ===")

        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "All linked accounts refreshed.",
                    "updated_accounts": updated_accounts,
                    "refreshed_counts": refreshed_counts,
                    "errors": list(error_map.values()),
                }
            ),
            200,
        )

    except Exception as ex:
        logger.error("Error in refresh_accounts")
        return jsonify({"error": str(ex)}), 500


@accounts.route("/<account_id>/refresh", methods=["POST"])
def refresh_single_account(account_id):
    """Refresh a single Plaid-linked account for its enabled product set."""
    from app.sql import account_logic

    data = request.get_json() or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    account = Account.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"status": "error", "message": "Account not found"}), 404

    updated = False

    if account.link_type != "Plaid":
        return (
            jsonify({"status": "error", "message": "Unsupported link type"}),
            400,
        )

    token = getattr(account.plaid_account, "access_token", None)
    if not token:
        return (
            jsonify({"status": "error", "message": "Missing Plaid token"}),
            400,
        )
    products = _plaid_products_for_account(account)
    plaid_updated = False

    for product_name in products:
        if product_name == "transactions":
            updated_flag, err = account_logic.refresh_data_for_plaid_account(
                token,
                account_id,
                start_date=start_date,
                end_date=end_date,
            )

            if err and err.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED":
                logger.warning(
                    f"Plaid re-auth required for account {account.account_id}: {err.get('plaid_error_message')}. "
                    "User must re-auth via Link update mode. Call POST /api/plaid/transactions/generate_update_link_token with account_id."
                )
                return (
                    jsonify(
                        {
                            "status": "success",
                            "updated": False,
                            "requires_reauth": True,
                            "update_link_token_endpoint": "/api/plaid/transactions/generate_update_link_token",
                            "account_id": account.account_id,
                            "error": {
                                "code": err.get("plaid_error_code"),
                                "message": err.get("plaid_error_message"),
                            },
                        }
                    ),
                    200,
                )
            if err:
                logger.error(
                    "Plaid error on single account refresh %s: %s",
                    account.account_id,
                    err,
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "updated": False,
                            "message": f"Plaid error: {err.get('plaid_error_message', 'Unknown error')}",
                            "error": err,
                        }
                    ),
                    502,
                )
            plaid_updated = plaid_updated or updated_flag
            if updated_flag and account.plaid_account:
                account.plaid_account.last_refreshed = datetime.now(timezone.utc)
        elif product_name == "investments":
            try:
                investments_updated = _refresh_plaid_investments(
                    account,
                    token,
                    start_date=start_date,
                    end_date=end_date,
                )
                plaid_updated = plaid_updated or investments_updated
                if account.plaid_account:
                    account.plaid_account.last_refreshed = datetime.now(timezone.utc)
            except Exception as exc:
                logger.error(
                    "Plaid investments refresh failed for account %s: %s",
                    account.account_id,
                    exc,
                    exc_info=True,
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "updated": False,
                            "message": "Plaid investments refresh failed.",
                        }
                    ),
                    502,
                )
        else:
            logger.info(
                "Skipping unsupported Plaid product %s for account %s",
                product_name,
                account.account_id,
            )

    updated = plaid_updated

    if updated:
        db.session.commit()
    else:
        db.session.rollback()

    return jsonify({"status": "success", "updated": updated}), 200


@accounts.route("/get_accounts", methods=["GET"])
def get_accounts():
    try:
        include_hidden = request.args.get("include_hidden", "false").lower() == "true"
        query = Account.query
        if not include_hidden:
            query = query.filter(Account.is_hidden.is_(False))
        accounts = query.all()
        data = []
        for a in accounts:
            try:
                last_refreshed = None
                if a.plaid_account and a.plaid_account.last_refreshed:
                    last_refreshed = a.plaid_account.last_refreshed
                normalized_balance = normalize_account_balance(a.balance, a.type)
                balance_value = (
                    float(normalized_balance)
                    if normalized_balance is not None
                    else None
                )
                logger.info(
                    f"Normalized original balance of {a.balance} to {normalized_balance} because account type {a.type}"
                )

                data.append(
                    {
                        "id": a.id,
                        "account_id": a.account_id,
                        "name": a.name,
                        "institution_name": a.institution_name,
                        "type": a.type,
                        "balance": balance_value,
                        "adjusted_balance": balance_value,
                        "subtype": a.subtype,
                        "link_type": a.link_type,
                        "last_refreshed": last_refreshed,
                        "is_hidden": a.is_hidden,
                    }
                )
            except Exception as item_err:
                logger.warning(
                    f"Error serializing account ID {a.id}: {item_err}", exc_info=True
                )
        return jsonify({"status": "success", "accounts": data}), 200
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/recurring", methods=["GET"])
def get_recurring(account_id):
    """
    Endpoint to get merged recurring transactions for a given account.
    Retrieves all recurring transactions for the specified account from the database.
    """
    try:
        recurring_txs = RecurringTransaction.query.filter_by(
            account_id=account_id
        ).all()
        data = []
        for tx in recurring_txs:
            amount = display_transaction_amount(getattr(tx, "transaction", tx))
            data.append(
                {
                    "id": tx.id,
                    "description": tx.description,
                    "amount": amount,
                    "frequency": tx.frequency,
                    "next_due_date": (
                        tx.next_due_date.isoformat() if tx.next_due_date else None
                    ),
                    "notes": tx.notes,
                    "updated_at": tx.updated_at.isoformat() if tx.updated_at else None,
                }
            )
        return jsonify({"status": "success", "reminders": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """
    Endpoint to update a recurring transaction for a given account.
    Expects JSON payload with at least an "amount" field.
    If no recurring transaction exists for the account, a new one is created.
    """
    data = request.get_json()
    if not data or "amount" not in data:
        return (
            jsonify({"status": "error", "message": "Missing 'amount' in request body"}),
            400,
        )

    amount = data["amount"]
    try:
        recurring = RecurringTransaction.query.filter_by(account_id=account_id).first()
        if recurring:
            recurring.amount = amount
            db.session.commit()
            return (
                jsonify(
                    {"status": "success", "message": "Recurring transaction updated"}
                ),
                200,
            )
        else:
            # Create a new recurring transaction with a default description and frequency if not provided.
            description = data.get("description", "Recurring Transaction")
            frequency = data.get("frequency", "monthly")
            new_tx = RecurringTransaction(
                account_id=account_id,
                description=description,
                amount=amount,
                frequency=frequency,
            )
            db.session.add(new_tx)
            db.session.commit()
            return (
                jsonify(
                    {"status": "success", "message": "Recurring transaction created"}
                ),
                201,
            )
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/hidden", methods=["PUT"])
def set_account_hidden(account_id):
    """Toggle an account's hidden status."""
    data = request.get_json() or {}
    hidden = bool(data.get("hidden", True))
    try:
        account = Account.query.filter_by(account_id=account_id).first()
        if not account:
            return (
                jsonify({"status": "error", "message": "Account not found"}),
                404,
            )
        account.is_hidden = hidden
        db.session.commit()
        update_account_history(
            account_id=account.account_id,
            user_id=account.user_id,
            balance=account.balance,
            is_hidden=account.is_hidden,
        )
        return jsonify({"status": "success", "hidden": account.is_hidden}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/match", methods=["POST"])
def match_account_by_fields():
    try:
        data = request.get_json()
        query = Account.query

        filters = []
        if data.get("account_id"):
            filters.append(Account.account_id == data["account_id"])
        if data.get("name"):
            filters.append(Account.name.ilike(f"%{data['name']}%"))
        if data.get("institution_name"):
            filters.append(
                Account.institution_name.ilike(f"%{data['institution_name']}%")
            )
        if data.get("type"):
            filters.append(Account.type == data["type"])
        if data.get("subtype"):
            filters.append(Account.subtype == data["subtype"])

        if filters:
            from sqlalchemy import or_

            matches = query.filter(or_(*filters)).all()
        else:
            matches = []

        return jsonify(
            [
                {
                    "account_id": acc.account_id,
                    "name": acc.name,
                    "institution_name": acc.institution_name,
                    "type": acc.type,
                    "subtype": acc.subtype,
                }
                for acc in matches
            ]
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/<account_id>/net_changes", methods=["GET"])
def account_net_changes(account_id):
    """Return net balance change for an account between two dates.

    The endpoint expects ``start_date`` and ``end_date`` query parameters
    in ``YYYY-MM-DD`` format and computes the difference between the
    account's ending and starting balances using :class:`AccountHistory`
    records.
    """

    try:
        from app.sql import account_logic

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        if not start_date_str or not end_date_str:
            return (
                jsonify({"error": "start_date and end_date are required"}),
                400,
            )

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        data = account_logic.get_net_change(account_id, start_date, end_date)
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error in account_net_changes: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Endpoint to fetch account balance history
@accounts.route("/<account_id>/history", methods=["GET"])
def get_account_history(account_id):
    """Return reverse-mapped daily balance history for an account.

    The calculation starts from the account's current balance and walks
    backwards through transaction deltas to derive prior day balances.
    A ``range`` query parameter like ``7d`` or ``30d`` limits how many
    days are returned when explicit ``start_date`` and ``end_date``
    parameters are not provided. Both the external ``account_id`` and
    internal numeric ``id`` are accepted in the path segment.
    """
    from datetime import timedelta

    from app.services.account_history import compute_balance_history
    from sqlalchemy import func

    try:
        range_param = request.args.get("range", "30d")
        days = int(range_param.rstrip("d")) if range_param.endswith("d") else 30

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        now_date = datetime.now(timezone.utc).date()
        start_date = None
        end_date = None

        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return (
                    jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}),
                    400,
                )
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return (
                    jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD"}),
                    400,
                )

        if start_date and end_date:
            pass
        elif start_date and not end_date:
            end_date = start_date + timedelta(days=days - 1)
        elif end_date and not start_date:
            start_date = end_date - timedelta(days=days - 1)
        else:
            end_date = now_date
            start_date = end_date - timedelta(days=days - 1)

        # Use the robust account resolver
        account = resolve_account_by_any_id(account_id)
        if not account:
            logger.warning(f"Account history request for unknown account: {account_id}")
            return jsonify({"error": "Account not found"}), 404

        tx_rows = (
            db.session.query(func.date(Transaction.date), func.sum(Transaction.amount))
            .filter(Transaction.account_id == account.account_id)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
            .group_by(func.date(Transaction.date))
            .all()
        )

        txs = [{"date": row[0], "amount": float(row[1])} for row in tx_rows]

        balances = compute_balance_history(account.balance, txs, start_date, end_date)

        return (
            jsonify(
                {
                    "accountId": account.account_id,
                    "asOfDate": end_date.isoformat(),
                    "balances": balances,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error(f"Error in get_account_history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@accounts.route("/<account_id>/transaction_history", methods=["GET"])
def transaction_history(account_id):
    """Return transaction history for an account.

    Provides a paginated list of transactions for the specified account.
    Supports filtering by date range and excludes internal transactions by default.
    Both external account_id and internal numeric ID are accepted.

    Query Parameters:
        start_date (str, optional): Filter transactions after this date (YYYY-MM-DD)
        end_date (str, optional): Filter transactions before this date (YYYY-MM-DD)
        limit (int, optional): Maximum number of transactions to return (default: 100, max: 1000)
        offset (int, optional): Number of transactions to skip for pagination (default: 0)
        order (str, optional): Sort order - 'desc' (newest first) or 'asc' (oldest first) (default: 'desc')
        include_internal (bool, optional): Whether to include internal transactions (default: false)
    """
    try:
        # Resolve account using the robust resolver
        account = resolve_account_by_any_id(account_id)
        if not account:
            logger.warning(
                f"Transaction history request for unknown account: {account_id}"
            )
            return jsonify({"status": "error", "message": "Account not found"}), 404

        # Parse query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        limit = min(int(request.args.get("limit", 100)), 1000)  # Cap at 1000
        offset = int(request.args.get("offset", 0))
        order = request.args.get("order", "desc").lower()
        include_internal = (
            request.args.get("include_internal", "false").lower() == "true"
        )

        # Parse date filters
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Invalid start_date format. Use YYYY-MM-DD",
                        }
                    ),
                    400,
                )

        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Invalid end_date format. Use YYYY-MM-DD",
                        }
                    ),
                    400,
                )

        # Build query
        query = Transaction.query.filter(Transaction.account_id == account.account_id)

        # Apply date filters
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        # Exclude internal transactions unless requested
        if not include_internal:
            query = query.filter(
                (Transaction.is_internal.is_(False))
                | (Transaction.is_internal.is_(None))
            )

        # Apply ordering
        if order == "asc":
            query = query.order_by(Transaction.date.asc(), Transaction.id.asc())
        else:
            query = query.order_by(Transaction.date.desc(), Transaction.id.desc())

        # Get total count (before limit/offset)
        total_count = query.count()

        # Apply pagination
        transactions = query.offset(offset).limit(limit).all()

        # Format transaction data
        transaction_data = []
        for tx in transactions:
            tx_dict = {
                "id": tx.id,
                "account_id": tx.account_id,
                "date": tx.date.isoformat() if tx.date else None,
                "description": getattr(tx, "name", None)
                or getattr(tx, "description", None)
                or getattr(tx, "merchant_name", None),
                "amount": float(tx.amount) if tx.amount is not None else 0.0,
                "category": getattr(tx, "category", None),
                "is_internal": getattr(tx, "is_internal", False),
            }

            # Add any additional metadata that's available
            if hasattr(tx, "merchant_name") and tx.merchant_name:
                tx_dict["merchant_name"] = tx.merchant_name
            if hasattr(tx, "transaction_type") and tx.transaction_type:
                tx_dict["transaction_type"] = tx.transaction_type
            if hasattr(tx, "plaid_transaction_id") and tx.plaid_transaction_id:
                tx_dict["plaid_transaction_id"] = tx.plaid_transaction_id

            transaction_data.append(tx_dict)

        # Build pagination info
        has_more = (offset + limit) < total_count
        next_offset = offset + limit if has_more else None

        logger.info(
            f"Retrieved {len(transaction_data)} transactions for account {account.account_id} (offset: {offset}, total: {total_count})"
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "account_id": account.account_id,
                    "transactions": transaction_data,
                    "paging": {
                        "limit": limit,
                        "offset": offset,
                        "total_count": total_count,
                        "has_more": has_more,
                        "next_offset": next_offset,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(
            f"Error in transaction_history for account {account_id}: {e}", exc_info=True
        )
        return (
            jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}),
            500,
        )
