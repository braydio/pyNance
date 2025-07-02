"""Institution grouping and refresh endpoints."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.config import FILES, TELLER_API_BASE_URL
from app.models import Institution
from app.helpers.teller_helpers import load_tokens
from app.sql import account_logic, transactions_logic
from app.utils.finance_utils import normalize_account_balance

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
            elif acc.teller_account and acc.teller_account.last_refreshed:
                refreshed = acc.teller_account.last_refreshed
            if refreshed and (last_refreshed is None or refreshed > last_refreshed):
                last_refreshed = refreshed
            accounts.append(
                {
                    "account_id": acc.account_id,
                    "name": acc.name,
                    "type": acc.type,
                    "subtype": acc.subtype,
                    "balance": normalize_account_balance(acc.balance, acc.type),
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
    tokens = load_tokens()

    for account in inst.accounts:
        updated = False
        if account.link_type == "Plaid":
            token = getattr(account.plaid_account, "access_token", None)
            if not token:
                continue
            updated = transactions_logic.refresh_data_for_plaid_account(
                token,
                account.account_id,
                start_date=start_date,
                end_date=end_date,
            )
            if updated and account.plaid_account:
                # Use non-deprecated current time
                account.plaid_account.last_refreshed = datetime.now()
        elif account.link_type == "Teller":
            access_token = None
            for t in tokens:
                if t.get("user_id") == account.user_id:
                    access_token = t.get("access_token")
                    break
            if not access_token and account.teller_account:
                access_token = account.teller_account.access_token
            if not access_token:
                continue
            updated = transactions_logic.refresh_data_for_teller_account(
                account,
                access_token,
                FILES["TELLER_DOT_CERT"],
                FILES["TELLER_DOT_KEY"],
                TELLER_API_BASE_URL,
                start_date=start_date,
                end_date=end_date,
            )
            if updated and account.teller_account:
                # Use non-deprecated current time
                account.teller_account.last_refreshed = datetime.now()
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
