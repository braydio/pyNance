"""Institution grouping and refresh endpoints."""

from __future__ import annotations

from datetime import datetime
from app.config import logger

from app.extensions import db
from app.models import Institution
from app.sql import account_logic
from app.utils.finance_utils import normalize_account_balance
from app.helpers.plaid_helpers import get_accounts
from flask import Blueprint, jsonify, request

institutions = Blueprint("institutions", __name__)


@institutions.route("/", methods=["GET"])
def list_institutions():
    """Return institutions with aggregated account info."""
    data = []
    for inst in Institution.query.all():
        accounts = []
        last_refreshed = None
        for acc in inst.accounts:
            refreshed = None
            if acc.plaid_account and acc.plaid_account.last_refreshed:
                refreshed = acc.plaid_account.last_refreshed
            if refreshed and (last_refreshed is None or refreshed > last_refreshed):
                last_refreshed = refreshed
            accounts.append(
                {
                    "account_id": acc.account_id,
                    "name": acc.name,
                    "type": acc.type,
                    "subtype": acc.subtype,
                    "balance": float(normalize_account_balance(acc.balance, acc.type)),
                    "link_type": acc.link_type,
                }
            )
        data.append(
            {
                "id": inst.id,
                "name": inst.name,
                "provider": inst.provider,
                "last_refreshed": last_refreshed,
                "accounts": accounts,
            }
        )
    return jsonify({"status": "success", "institutions": data})


@institutions.route("/<int:institution_id>/refresh", methods=["POST"])
def refresh_institution(institution_id: int):
    """Refresh all accounts for the given institution."""
    inst = Institution.query.get_or_404(institution_id)
    data = request.get_json() or {}
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    updated_accounts = []
    refreshed_counts: dict[str, int] = {}
    token_account_cache: dict[str, list] = {}
    for account in inst.accounts:
        updated = False
        # Accept both 'plaid' and 'Plaid' values
        if str(getattr(account, "link_type", "")).lower() == "plaid":
            token = getattr(account.plaid_account, "access_token", None)
            if not token:
                continue
            accounts_data = token_account_cache.get(token)
            if accounts_data is None:
                accounts_data = get_accounts(token, account.user_id)
                if accounts_data is None:
                    logger.warning(
                        "Plaid rate limit hit; skipping institution account %s", account.account_id
                    )
                    continue
                accounts_data = [
                    item.to_dict() if hasattr(item, "to_dict") else dict(item)
                    for item in accounts_data
                ]
                token_account_cache[token] = accounts_data
            updated, _ = account_logic.refresh_data_for_plaid_account(
                token,
                account,
                accounts_data=accounts_data,
                start_date=start_date,
                end_date=end_date,
            )
            if updated and account.plaid_account:
                # Use non-deprecated current time
                account.plaid_account.last_refreshed = datetime.now()
        if updated:
            updated_accounts.append(account.name)
            refreshed_counts[inst.name] = refreshed_counts.get(inst.name, 0) + 1
    if updated_accounts:
        # Use non-deprecated current time
        inst.last_refreshed = datetime.now()
        db.session.commit()
    else:
        db.session.rollback()
    return (
        jsonify(
            {
                "status": "success",
                "updated_accounts": updated_accounts,
                "refreshed_counts": refreshed_counts,
            }
        ),
        200,
    )
