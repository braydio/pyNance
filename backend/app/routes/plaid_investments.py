"""Routes for Plaid investments flows and account syncing."""

from flask import Blueprint, jsonify, request

from app.config import logger
from app.extensions import db
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
)
from app.models import PlaidAccount, PlaidItem
from app.sql import investments_logic
from app.sql.account_logic import (
    canonicalize_plaid_products,
    mark_refresh_failure,
    mark_refresh_success,
    save_plaid_account,
    upsert_accounts,
)

plaid_investments = Blueprint("plaid_investments", __name__)


def _has_investments_scope(plaid_account: PlaidAccount) -> bool:
    """Return whether a Plaid account includes the investments product scope."""

    return "investments" in set(canonicalize_plaid_products(getattr(plaid_account, "product", None)))


def _request_json_dict():
    """Return the incoming request JSON body as a dictionary.

    The route contracts for this module expect object-like payloads. Any empty,
    malformed, or non-object JSON payloads are normalized to an empty dict so
    required-field validation can deterministically return 400 responses.
    """
    data = request.get_json(silent=True) or {}
    return data if isinstance(data, dict) else {}


@plaid_investments.route("/generate_link_token", methods=["POST"])
def generate_link_token_investments():
    """
    Generate a Plaid link token for the investments product.
    Expects JSON payload with "user_id". Malformed JSON is treated as empty input.
    """
    data = _request_json_dict()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        token = generate_link_token(user_id, products=["investments"])
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error("Error generating investments link token: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_investments():
    """
    Exchange a public token for an access token for investments.
    Expects JSON with "user_id" and "public_token". Malformed JSON is treated as empty input.
    """
    data = _request_json_dict()
    user_id = data.get("user_id")
    public_token = data.get("public_token")
    if not user_id or not public_token:
        return jsonify({"error": "Missing user_id or public_token"}), 400
    try:
        exchange_resp = exchange_public_token(public_token)
        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        if not access_token or not item_id:
            return jsonify({"error": "Failed to exchange public token"}), 500
        accounts = get_accounts(access_token, user_id)
        upsert_accounts(
            user_id,
            accounts,
            provider="plaid",
            access_token=access_token,
            enabled_products=["investments"],
        )
        for acct in accounts:
            acct_id = acct.get("account_id")
            if acct_id:
                save_plaid_account(acct_id, item_id, access_token, "investments")
        # Ensure 1 entry per Item in secure table
        try:
            existing_item = PlaidItem.query.filter_by(item_id=item_id).first()
            if existing_item:
                existing_item.access_token = access_token
                existing_item.user_id = str(user_id)
                existing_item.product = "investments"
                existing_item.is_active = True
            else:
                db.session.add(
                    PlaidItem(
                        user_id=str(user_id),
                        item_id=item_id,
                        access_token=access_token,
                        institution_name=None,
                        product="investments",
                        is_active=True,
                    )
                )
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to upsert PlaidItem for investments: %s", e)
        # Save initial investments data (if you have specific logic, call it here)
        # e.g., account_logic.save_investments_data(user_id, access_token)
        return (
            jsonify(
                {
                    "status": "success",
                    "item_id": item_id,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error("Error exchanging investments public token: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/refresh", methods=["POST"])
def refresh_investments_endpoint():
    """
    Refresh investments holdings for a linked investments item.
    Expects JSON with "user_id" and "item_id". Malformed JSON is treated as empty input.
    """
    data = _request_json_dict()
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    if not user_id or not item_id:
        return jsonify({"error": "Missing user_id or item_id"}), 400
    try:
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        # Default to last 30 days if not provided
        if not start_date or not end_date:
            from datetime import date, timedelta

            end_date = date.today().isoformat()
            start_date = (date.today() - timedelta(days=30)).isoformat()
        item_accounts = PlaidAccount.query.filter_by(item_id=item_id).all()
        account = next(
            (plaid_account for plaid_account in item_accounts if _has_investments_scope(plaid_account)),
            None,
        )
        if not account:
            return jsonify({"error": "Investments account not found"}), 404
        summary = investments_logic.sync_investments_from_plaid(
            user_id,
            account.access_token,
            start_date,
            end_date,
            commit=False,
        )
        mark_refresh_success(account, commit=False)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "upserts": summary,
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error("Error refreshing investments: %s", e, exc_info=True)
        mark_refresh_failure(account if "account" in locals() else None, e, commit=True)
        return jsonify({"error": str(e)}), 500


@plaid_investments.route("/refresh_all", methods=["POST"])
def refresh_all_investments():
    """Refresh holdings and transactions for all active Plaid investment items.

    Optional JSON body accepts start_date/end_date (YYYY-MM-DD); defaults last 30 days.
    """
    try:
        data = _request_json_dict()
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if not start_date or not end_date:
            from datetime import date, timedelta

            end_date = date.today().isoformat()
            start_date = (date.today() - timedelta(days=30)).isoformat()

        item_candidates = PlaidAccount.query.filter_by(is_active=True).all()
        items = [item for item in item_candidates if _has_investments_scope(item)]
        total = {
            "securities": 0,
            "holdings": 0,
            "investment_transactions": 0,
            "items": len(items),
        }
        for pa in items:
            try:
                sums = investments_logic.sync_investments_from_plaid(
                    pa.account.user_id if pa.account else None,
                    pa.access_token,
                    start_date,
                    end_date,
                    commit=False,
                )
                mark_refresh_success(pa, commit=False)
                db.session.commit()
                for k in ("securities", "holdings", "investment_transactions"):
                    total[k] += int(sums.get(k, 0))
            except Exception as inner:
                db.session.rollback()
                logger.error(
                    "Failed to refresh investments for item %s: %s",
                    pa.item_id,
                    inner,
                )
                mark_refresh_failure(pa, inner, commit=True)
                continue

        return (
            jsonify(
                {
                    "status": "success",
                    "summary": total,
                    "range": {"start_date": start_date, "end_date": end_date},
                }
            ),
            200,
        )
    except Exception as e:
        db.session.rollback()
        logger.error("Error in refresh_all_investments: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500
