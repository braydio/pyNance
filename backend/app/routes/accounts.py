"""Account management and refresh routes."""

import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app.config import logger
from app.extensions import db
from app.models import Account, PlaidItem, RecurringTransaction, Transaction
from app.services.accounts_service import fetch_accounts
from app.sql.account_logic import (
    canonicalize_plaid_products,
    refresh_is_stale,
    serialized_refresh_status,
    should_throttle_refresh,
)
from app.sql.forecast_logic import update_account_history
from app.utils.finance_utils import (
    display_transaction_amount,
    normalize_account_balance,
)
from flask import Blueprint, g, jsonify, request

# Blueprint for generic accounts routes
accounts = Blueprint("accounts", __name__)

INSTITUTION_STAGGER_SECONDS = 0.35


def _to_iso(dt):
    if not dt:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    try:
        return datetime.fromisoformat(str(dt)).isoformat()
    except Exception:
        return str(dt)


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
    """Return Plaid product identifiers from canonical or legacy storage."""

    return set(canonicalize_plaid_products(value))


def _plaid_products_for_account(account: Account) -> set[str]:
    """Return Plaid products enabled for the provided account.

    Unions account-level and item-level scopes using canonical scope parsing.
    """

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


def _is_plaid_link_type(value) -> bool:
    """Return True if the link_type value denotes Plaid (case-insensitive)."""
    try:
        return str(value or "").lower() == "plaid"
    except Exception:
        return False


@accounts.route("/refresh_accounts", methods=["POST"])
def refresh_all_accounts():
    """Refresh all linked accounts for their enabled products."""
    cached_response = getattr(g, "bulk_refresh_response", None)
    if cached_response is not None:
        logger.debug("Skipping duplicate bulk refresh call in the same request.")
        return cached_response
    try:
        from app.sql import account_logic

        data = request.get_json() or {}
        account_ids = data.get("account_ids") or []
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        logger.info(
            "[REFRESH][bulk] starting | account_ids=%s | start=%s | end=%s",
            account_ids if account_ids else "all",
            start_date,
            end_date,
        )

        query = Account.query
        if account_ids:
            query = query.filter(Account.account_id.in_(account_ids))
        accounts = sorted(
            query.all(),
            key=lambda acc: ((acc.institution_name or "").lower(), acc.account_id),
        )
        updated_accounts = []
        refreshed_counts: dict[str, int] = {}
        error_map: dict[tuple[str, str, str], dict] = {}
        skipped_non_plaid = 0
        missing_tokens = 0
        skipped_rate_limited = 0
        previous_institution = None
        token_account_cache: dict[str, list] = {}

        for account in accounts:
            inst = account.institution_name or "Unknown"
            if _is_plaid_link_type(account.link_type):
                access_token = None
                if account.plaid_account:
                    access_token = account.plaid_account.access_token
                if not access_token:
                    missing_tokens += 1
                    logger.warning("No Plaid token for institution %s", inst)
                    continue

                logger.debug("Refreshing Plaid accounts for institution %s", inst)
                if should_throttle_refresh(account.plaid_account):
                    skipped_rate_limited += 1
                    logger.info(
                        "Skipping Plaid refresh due to active cooldown | institution=%s",
                        inst,
                    )
                    continue
                if previous_institution and inst != previous_institution:
                    time.sleep(INSTITUTION_STAGGER_SECONDS)
                previous_institution = inst
                accounts_data = token_account_cache.get(access_token)
                if accounts_data is None:
                    accounts_data = fetch_accounts(access_token, account.user_id)
                    if accounts_data is None:
                        skipped_rate_limited += 1
                        logger.info(
                            "Skipping refresh due to Plaid rate limit | institution=%s",
                            inst,
                        )
                        continue
                    accounts_data = [
                        acct.to_dict() if hasattr(acct, "to_dict") else dict(acct)
                        for acct in accounts_data
                    ]
                    token_account_cache[access_token] = accounts_data
                products = _plaid_products_for_account(account)
                account_updated = False

                for product_name in products:
                    if product_name == "transactions":
                        updated, err = account_logic.refresh_data_for_plaid_account(
                            access_token,
                            account,
                            accounts_data=accounts_data,
                            start_date=start_date,
                            end_date=end_date,
                        )
                        if err:
                            err_payload = (
                                err
                                if isinstance(err, dict)
                                else {
                                    "plaid_error_code": err,
                                    "plaid_error_message": str(err),
                                }
                            )
                            key = (
                                inst,
                                err_payload.get("plaid_error_code"),
                                err_payload.get("plaid_error_message"),
                            )
                            if key not in error_map:
                                error_map[key] = {
                                    "institution_name": inst,
                                    "account_ids": [account.account_id],
                                    "account_names": [account.name],
                                    "plaid_error_code": err_payload.get(
                                        "plaid_error_code"
                                    ),
                                    "plaid_error_message": err_payload.get(
                                        "plaid_error_message"
                                    ),
                                }

                                if (
                                    err_payload.get("plaid_error_code")
                                    == "ITEM_LOGIN_REQUIRED"
                                ):
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

                                if (
                                    err_payload.get("plaid_error_code")
                                    == "ITEM_LOGIN_REQUIRED"
                                ):
                                    affected_ids = set(
                                        error_map[key].get("affected_account_ids", [])
                                    )
                                    affected_ids.add(account.account_id)
                                    error_map[key]["affected_account_ids"] = list(
                                        affected_ids
                                    )

                            if (
                                err_payload.get("plaid_error_code")
                                == "ITEM_LOGIN_REQUIRED"
                            ):
                                logger.warning(
                                    "Plaid re-auth required: Institution: %s, Account: %s, Error: %s. "
                                    "User must re-auth via Link update mode. Call POST "
                                    "/api/plaid/transactions/generate_update_link_token with account_id.",
                                    inst,
                                    account.name,
                                    err_payload.get("plaid_error_message"),
                                )
                            else:
                                logger.error(
                                    "Plaid refresh error | institution=%s | account=%s | code=%s | message=%s",
                                    inst,
                                    account.name,
                                    err_payload.get("plaid_error_code"),
                                    err_payload.get("plaid_error_message"),
                                )
                        else:
                            account_updated = account_updated or updated
                            if updated and account.plaid_account:
                                # Store naive timestamp to match column type
                                account.plaid_account.last_refreshed = datetime.now()
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
                                # Store naive timestamp to match column type
                                account.plaid_account.last_refreshed = datetime.now()
                        except Exception as exc:
                            # Ensure the session is usable for the rest of the loop
                            try:
                                db.session.rollback()
                            except Exception:
                                pass
                            logger.error(
                                "Plaid investments refresh failed for institution %s: %s",
                                inst,
                                exc,
                                exc_info=True,
                            )
                    else:
                        logger.info(
                            "Skipping unsupported Plaid product %s for institution %s",
                            product_name,
                            inst,
                        )

                if account_updated:
                    updated_accounts.append(account.name)
                    refreshed_counts[inst] = refreshed_counts.get(inst, 0) + 1

            else:
                skipped_non_plaid += 1

        # Log aggregated error summary for operators
        if error_map:
            error_lines = []
            for key, error_info in error_map.items():
                institution, error_code, error_message = key
                affected_count = len(error_info["account_ids"])
                account_names = ", ".join(
                    error_info["account_names"][:3]
                )  # Show first 3 names
                if len(error_info["account_names"]) > 3:
                    account_names += f" and {len(error_info['account_names']) - 3} more"

                remediation = ""
                if error_code == "ITEM_LOGIN_REQUIRED":
                    remediation = (
                        " | Remediation: User must re-auth via Link update mode. "
                        "Call POST /api/plaid/transactions/generate_update_link_token with account_id."
                    )

                error_lines.append(
                    (
                        f"{institution}: {error_code} - {error_message} "
                        f"affected={affected_count} ({account_names}){remediation}"
                    )
                )

            logger.info("[REFRESH][bulk] error summary | %s", " | ".join(error_lines))

        db.session.commit()
        logger.info(
            (
                "[REFRESH][bulk] completed | total=%d | updated=%d | "
                "institutions=%d | missing_tokens=%d | non_plaid_skipped=%d | "
                "rate_limited_skipped=%d | errors=%d"
            ),
            len(accounts),
            len(updated_accounts),
            len(refreshed_counts),
            missing_tokens,
            skipped_non_plaid,
            skipped_rate_limited,
            len(error_map),
        )
        response = (
            jsonify(
                {
                    "status": "success",
                    "message": "All linked accounts refreshed.",
                    "updated_accounts": updated_accounts,
                    "refreshed_counts": refreshed_counts,
                    "rate_limited_skipped": skipped_rate_limited,
                    "errors": list(error_map.values()),
                }
            ),
            200,
        )
        g.bulk_refresh_response = response
        return response

    except Exception as ex:
        logger.error("Error in refresh_accounts: %s", ex, exc_info=True)
        response = (jsonify({"error": str(ex)}), 500)
        g.bulk_refresh_response = response
        return response


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

    inst = account.institution_name or "Unknown"
    logger.info(
        "[REFRESH][single] starting | institution=%s | start=%s | end=%s",
        inst,
        start_date,
        end_date,
    )

    updated = False

    if str(getattr(account, "link_type", "")).lower() != "plaid":
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
    accounts_data = fetch_accounts(token, account.user_id)
    if accounts_data is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Plaid rate limit hit; try again shortly.",
                    "code": "PLAID_RATE_LIMIT",
                }
            ),
            429,
        )
    accounts_data = [
        acct.to_dict() if hasattr(acct, "to_dict") else dict(acct)
        for acct in accounts_data
    ]
    if should_throttle_refresh(account.plaid_account):
        status = serialized_refresh_status(account.plaid_account)
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Plaid rate limit cooldown active. Try again shortly.",
                    "cooldown_until": status.get("cooldown_until"),
                }
            ),
            429,
        )
    products = _plaid_products_for_account(account)
    plaid_updated = False

    for product_name in products:
        if product_name == "transactions":
            updated_flag, err = account_logic.refresh_data_for_plaid_account(
                token,
                account,
                accounts_data=accounts_data,
                start_date=start_date,
                end_date=end_date,
            )

            if (
                isinstance(err, dict)
                and err.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED"
            ):
                logger.warning(
                    "Plaid re-auth required for institution %s (account %s): %s. User must re-auth via Link update mode. "
                    "Call POST /api/plaid/transactions/generate_update_link_token with account_id.",
                    inst,
                    account.name,
                    err.get("plaid_error_message"),
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
                    "Plaid error on single account refresh for institution %s (account %s): %s",
                    inst,
                    account.name,
                    err,
                )
                err_payload = (
                    err
                    if isinstance(err, dict)
                    else {
                        "plaid_error_code": "unknown",
                        "plaid_error_message": str(err),
                    }
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "updated": False,
                            "message": f"Plaid error: {err_payload.get('plaid_error_message', 'Unknown error')}",
                            "error": err_payload,
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
                    # Store naive timestamp to match column type
                    account.plaid_account.last_refreshed = datetime.now()
            except Exception as exc:
                logger.error(
                    "Plaid investments refresh failed for institution %s: %s",
                    inst,
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
                "Skipping unsupported Plaid product %s for institution %s",
                product_name,
                inst,
            )

    updated = plaid_updated

    if updated:
        db.session.commit()
    else:
        db.session.rollback()

    logger.info(
        "[REFRESH][single] completed | institution=%s | updated=%s | products=%s",
        inst,
        updated,
        sorted(products),
    )

    return jsonify({"status": "success", "updated": updated}), 200


@accounts.route("/get_accounts", methods=["GET"])
def list_accounts():
    """Return serialized account data for the requesting client."""
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
                refresh_status = serialized_refresh_status(
                    getattr(a, "plaid_account", None)
                )
                cooldown_until = _to_iso(refresh_status.get("cooldown_until"))
                if a.plaid_account and a.plaid_account.last_refreshed:
                    last_refreshed = a.plaid_account.last_refreshed
                normalized_balance = normalize_account_balance(
                    a.balance, a.type, account_id=a.account_id
                )
                balance_value = (
                    float(normalized_balance)
                    if normalized_balance is not None
                    else None
                )
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(
                        "Normalized original balance of %s to %s because account type %s",
                        a.balance,
                        normalized_balance,
                        a.type,
                    )

                data.append(
                    {
                        # Account model uses string business key `account_id` as PK
                        # Maintain `id` field for frontend compatibility by mirroring `account_id`.
                        "id": a.account_id,
                        "account_id": a.account_id,
                        "name": a.name,
                        "display_name": a.display_name,
                        "institution_name": a.institution_name,
                        "type": a.type,
                        "balance": balance_value,
                        "adjusted_balance": balance_value,
                        "subtype": a.subtype,
                        "link_type": a.link_type,
                        "last_refreshed": _to_iso(last_refreshed),
                        "is_hidden": a.is_hidden,
                        "refresh_status": refresh_status,
                        "refresh_stale": refresh_is_stale(
                            getattr(a, "plaid_account", None)
                        ),
                        "refresh_cooldown_until": cooldown_until,
                    }
                )
            except Exception as item_err:
                try:
                    acct_identifier = getattr(a, "account_id", None)
                except Exception:
                    acct_identifier = None
                logger.warning(
                    "Error serializing account: %s - %s",
                    acct_identifier,
                    item_err,
                    exc_info=True,
                )
        return jsonify({"status": "success", "accounts": data}), 200
    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@accounts.route("/refresh_status", methods=["GET"])
def refresh_status():
    """Expose last refresh details for each Plaid-linked account."""

    include_hidden = request.args.get("include_hidden", "false").lower() == "true"
    sla_hours = float(request.args.get("sla_hours", 6))
    sla = timedelta(hours=sla_hours)

    query = Account.query
    if not include_hidden:
        query = query.filter(Account.is_hidden.is_(False))

    rows = []
    for acc in query.all():
        if str(getattr(acc, "link_type", "")).lower() != "plaid":
            continue

        pa = getattr(acc, "plaid_account", None)
        status = serialized_refresh_status(pa)
        cooldown_until = _to_iso(status.get("cooldown_until"))
        last_refreshed = getattr(pa, "last_refreshed", None) if pa else None
        rows.append(
            {
                "account_id": acc.account_id,
                "account_name": acc.name,
                "display_name": acc.display_name,
                "institution_name": acc.institution_name,
                "last_refreshed": _to_iso(last_refreshed),
                "refresh_status": status,
                "refresh_stale": refresh_is_stale(pa, sla=sla),
                "refresh_cooldown_until": cooldown_until,
            }
        )

    return jsonify({"status": "success", "accounts": rows}), 200


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
                    "display_name": acc.display_name,
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
    """Return net balance change and breakdown for an account.

    Query expects ``start_date`` and ``end_date`` (YYYY-MM-DD). Response includes
    income, expense, and net values for the period in a standard
    ``{"status": "success", "data": {...}}`` envelope for frontend use. For
    backward compatibility, legacy top-level keys (``account_id``,
    ``net_change``, ``period``) are also included.
    """

    try:
        from app.sql import account_logic
        from sqlalchemy import case, func

        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        if not start_date_str or not end_date_str:
            return (
                jsonify({"error": "start_date and end_date are required"}),
                400,
            )

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # Compute income/expense breakdown from transactions in the range
        # Use external account_id consistently
        income_sum = func.sum(
            case((Transaction.amount > 0, Transaction.amount), else_=0)
        )
        expense_sum = func.sum(
            case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)
        )

        q = (
            db.session.query(income_sum.label("income"), expense_sum.label("expenses"))
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= start_date)
            .filter(Transaction.date <= end_date)
        )
        row = q.first()
        income = float(getattr(row, "income", 0) or 0)
        expense = float(getattr(row, "expenses", 0) or 0)
        # Net as income - expense (expense is positive magnitude)
        net = round(income - expense, 2)

        # Legacy net change value based on AccountHistory snapshots
        # Some environments might not have snapshots for the exact dates yet;
        # treat that as 0 instead of raising to avoid breaking the UI.
        try:
            legacy = account_logic.get_net_change(account_id, start_date, end_date)
        except Exception:
            legacy = {
                "account_id": account_id,
                "net_change": net,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }

        payload = {
            "status": "success",
            "data": {
                "income": round(income, 2),
                "expense": round(expense, 2),
                "net": net,
            },
            # Backward-compat legacy fields
            "account_id": legacy.get("account_id", account_id),
            "net_change": legacy.get("net_change", net),
            "period": legacy.get(
                "period", {"start": start_date.isoformat(), "end": end_date.isoformat()}
            ),
        }

        return jsonify(payload), 200
    except Exception as e:
        logger.error("Error in account_net_changes: %s", e, exc_info=True)
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
    internal numeric ``id`` are accepted in the path segment. The
    response exposes the normalized ``balances`` array and a ``history``
    alias for legacy consumers.
    """

    from app.services.enhanced_account_history import get_or_compute_account_history

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
            logger.warning(
                "Account history request for unknown account: %s", account_id
            )
            return jsonify({"error": "Account not found"}), 404

        balances = get_or_compute_account_history(
            account.account_id,
            days=days,
            start_date=start_date,
            end_date=end_date,
            include_internal=False,
        )

        response_payload = {
            "accountId": account.account_id,
            "asOfDate": end_date.isoformat(),
            "balances": balances,
        }
        response_payload["history"] = response_payload["balances"]

        return jsonify(response_payload), 200
    except Exception as e:
        logger.error("Error in get_account_history: %s", e, exc_info=True)
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
                "Transaction history request for unknown account: %s", account_id
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
            "Retrieved %d transactions for institution %s (account %s) (offset: %d, total: %d)",
            len(transaction_data),
            account.institution_name or "Unknown",
            account.name,
            offset,
            total_count,
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
        inst = (
            (account.institution_name or "Unknown")
            if "account" in locals() and account
            else account_id
        )
        logger.error(
            "Error in transaction_history for institution %s: %s",
            inst,
            e,
            exc_info=True,
        )
        return (
            jsonify({"status": "error", "message": f"Internal server error: {str(e)}"}),
            500,
        )
