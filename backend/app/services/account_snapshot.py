"""Business logic for dashboard account snapshot preferences."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from app.extensions import db
from app.models import Account, AccountSnapshotPreference
from app.utils.finance_utils import normalize_account_balance

MAX_SNAPSHOT_SELECTION = 5
DEFAULT_USER_SCOPE = "default"


def build_snapshot_payload(user_id: str | None = None) -> dict:
    """Return persisted snapshot selection and associated account data."""
    scope = user_id or DEFAULT_USER_SCOPE
    accounts = _visible_accounts()
    preference = _ensure_preference(scope, accounts)
    normalized = _normalize_ids(preference.selected_account_ids)
    valid_ids, discarded = _filter_valid_ids(normalized, accounts)

    if valid_ids != normalized:
        preference.selected_account_ids = valid_ids
        db.session.commit()

    return _build_payload(accounts, preference, valid_ids, discarded)


def update_snapshot_selection(
    selected_account_ids: Iterable[str], user_id: str | None = None
) -> dict:
    """Persist a new snapshot selection and return the refreshed payload."""
    scope = user_id or DEFAULT_USER_SCOPE
    accounts = _visible_accounts()
    preference = _ensure_preference(scope, accounts)

    normalized = _normalize_ids(selected_account_ids)
    valid_ids, discarded = _filter_valid_ids(normalized, accounts)
    current_ids = preference.selected_account_ids or []

    if valid_ids != current_ids:
        preference.selected_account_ids = valid_ids
        db.session.commit()

    return _build_payload(accounts, preference, valid_ids, discarded)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _visible_accounts() -> List[Account]:
    return (
        Account.query.filter(Account.is_hidden.is_(False))
        .order_by(Account.institution_name.asc(), Account.name.asc())
        .all()
    )


def _ensure_preference(
    user_id: str, accounts: Sequence[Account]
) -> AccountSnapshotPreference:
    preference = AccountSnapshotPreference.query.filter_by(user_id=user_id).first()
    if preference:
        if preference.selected_account_ids is None:
            preference.selected_account_ids = []
            db.session.commit()
        return preference

    default_ids = [acc.account_id for acc in accounts if acc.account_id][
        :MAX_SNAPSHOT_SELECTION
    ]
    preference = AccountSnapshotPreference(
        user_id=user_id,
        selected_account_ids=default_ids,
    )
    db.session.add(preference)
    db.session.commit()
    return preference


def _normalize_ids(raw_ids: Iterable[str] | None) -> List[str]:
    if not raw_ids:
        return []
    seen: set[str] = set()
    result: List[str] = []
    for raw in raw_ids:
        if raw is None:
            continue
        value = str(raw).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _filter_valid_ids(
    ids: Sequence[str], accounts: Sequence[Account]
) -> Tuple[List[str], List[str]]:
    account_map = {
        acc.account_id: acc for acc in accounts if getattr(acc, "account_id", None)
    }
    valid: List[str] = []
    discarded: List[str] = []
    for account_id in ids:
        if account_id in account_map:
            valid.append(account_id)
        else:
            discarded.append(account_id)

    if len(valid) > MAX_SNAPSHOT_SELECTION:
        overflow = valid[MAX_SNAPSHOT_SELECTION:]
        discarded.extend(overflow)
        valid = valid[:MAX_SNAPSHOT_SELECTION]

    return valid, discarded


def _build_payload(
    accounts: Sequence[Account],
    preference: AccountSnapshotPreference,
    selected_ids: Sequence[str],
    discarded: Sequence[str],
) -> dict:
    account_map = {
        acc.account_id: acc for acc in accounts if getattr(acc, "account_id", None)
    }
    selected_accounts = [
        _serialize_account(account_map[account_id])
        for account_id in selected_ids
        if account_id in account_map
    ]
    available_accounts = [_serialize_account(acc) for acc in accounts]

    metadata = {
        "max_selection": MAX_SNAPSHOT_SELECTION,
        "preference_id": preference.id,
        "updated_at": _datetime_to_iso(preference.updated_at),
    }
    if discarded:
        metadata["discarded_ids"] = list(discarded)

    return {
        "selected_account_ids": list(selected_ids),
        "selected_accounts": selected_accounts,
        "available_accounts": available_accounts,
        "metadata": metadata,
    }


def _serialize_account(account: Account) -> dict:
    normalized_balance = normalize_account_balance(account.balance, account.type)
    last_refreshed = None
    plaid_account = getattr(account, "plaid_account", None)
    teller_account = getattr(account, "teller_account", None)

    if getattr(plaid_account, "last_refreshed", None):
        last_refreshed = _datetime_to_iso(plaid_account.last_refreshed)
    elif getattr(teller_account, "last_refreshed", None):
        last_refreshed = _datetime_to_iso(teller_account.last_refreshed)

    return {
        "id": account.id,
        "account_id": account.account_id,
        "name": account.name,
        "institution_name": account.institution_name,
        "type": account.type,
        "subtype": account.subtype,
        "link_type": account.link_type,
        "balance": normalized_balance,
        "adjusted_balance": normalized_balance,
        "last_refreshed": last_refreshed,
        "is_hidden": account.is_hidden,
    }


def _datetime_to_iso(value) -> str | None:
    if not value:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
