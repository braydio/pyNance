"""Service helpers for managing dashboard account groups."""

from __future__ import annotations

from typing import Sequence

from app.extensions import db
from app.models import (
    Account,
    AccountGroup,
    AccountGroupMembership,
    AccountGroupPreference,
)
from app.utils.finance_utils import normalize_account_balance

DEFAULT_USER_SCOPE = "default"
DEFAULT_GROUP_NAME = "Group"
DEFAULT_ACCENT = "var(--color-accent-cyan)"
MAX_ACCOUNTS_PER_GROUP = 5


def list_account_groups(user_id: str | None = None) -> dict:
    """Retrieve all account groups for a user.

    Args:
        user_id: Optional identifier for the user whose groups should be
            returned. When omitted the default scope is used.

    Returns:
        dict: A payload containing serialized groups and the active group ID.
    """

    scope = _resolve_scope(user_id)
    groups = _load_groups(scope)
    preference = _ensure_preference(scope, groups)
    serialized = _serialize_groups(groups)
    active_id = preference.active_group_id if preference else None
    if not active_id and serialized:
        active_id = serialized[0]["id"]
    if preference and active_id != preference.active_group_id:
        preference.active_group_id = active_id
        db.session.commit()
    return {"groups": serialized, "active_group_id": active_id}


def create_account_group(
    name: str | None = None,
    user_id: str | None = None,
    accent: str | None = None,
    group_id: str | None = None,
) -> dict:
    """Create a new group for a user.

    Args:
        name: Optional display name for the group.
        user_id: Optional identifier for the owning user.
        accent: Optional accent color for UI rendering.
        group_id: Optional identifier to persist, otherwise generated.

    Returns:
        dict: A payload with the persisted group and the active group ID.
    """

    scope = _resolve_scope(user_id)
    groups = _load_groups(scope)
    position = max((g.position for g in groups), default=-1) + 1
    group = AccountGroup(
        id=group_id,
        user_id=scope,
        name=(name or DEFAULT_GROUP_NAME).strip() or DEFAULT_GROUP_NAME,
        accent=accent or DEFAULT_ACCENT,
        position=position,
    )
    db.session.add(group)
    preference = _ensure_preference(scope, groups + [group])
    preference.active_group_id = group.id
    db.session.commit()
    data = _serialize_groups([group])[0]
    return {"group": data, "active_group_id": preference.active_group_id}


def update_account_group(
    group_id: str,
    *,
    user_id: str | None = None,
    name: str | None = None,
    accent: str | None = None,
) -> dict:
    """Update an existing group's metadata.

    Args:
        group_id: Identifier of the group to update.
        user_id: Optional identifier used to scope the lookup.
        name: Optional new display name for the group.
        accent: Optional accent color override.

    Returns:
        dict: Payload containing the refreshed group representation.

    Raises:
        ValueError: If the group does not exist for the provided scope.
    """

    group = _get_group(group_id, user_id=user_id)
    if name is not None:
        cleaned = name.strip()
        group.name = cleaned or DEFAULT_GROUP_NAME
    if accent is not None:
        group.accent = accent
    db.session.commit()
    return {"group": _serialize_groups([group])[0]}


def delete_account_group(group_id: str, user_id: str | None = None) -> dict:
    """Delete a group and resequence remaining groups.

    Args:
        group_id: Identifier of the group that should be removed.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the updated groups and active group ID.

    Raises:
        ValueError: If the group is not found for the provided scope.
    """

    scope = _resolve_scope(user_id)
    group = _get_group(group_id, user_id=scope)
    db.session.delete(group)
    db.session.flush()
    remaining = (
        AccountGroup.query.filter_by(user_id=scope)
        .order_by(AccountGroup.position.asc(), AccountGroup.created_at.asc())
        .all()
    )
    if not remaining:
        fallback = AccountGroup(
            user_id=scope,
            name=DEFAULT_GROUP_NAME,
            position=0,
            accent=DEFAULT_ACCENT,
        )
        db.session.add(fallback)
        remaining = [fallback]
    _resequence_groups(remaining)
    preference = _ensure_preference(scope, remaining)
    if preference.active_group_id not in {g.id for g in remaining}:
        preference.active_group_id = remaining[0].id if remaining else None
    db.session.commit()
    return {
        "groups": _serialize_groups(remaining),
        "active_group_id": preference.active_group_id,
    }


def reorder_account_groups(
    group_ids: Sequence[str], user_id: str | None = None
) -> dict:
    """Persist a new ordering for groups.

    Args:
        group_ids: Sequence of group identifiers in the desired order.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the reordered groups.

    Raises:
        ValueError: If the requested IDs do not match known groups.
    """

    scope = _resolve_scope(user_id)
    groups = _load_groups(scope)
    requested = list(group_ids)
    if set(requested) != {g.id for g in groups}:
        raise ValueError("Group list does not match existing records")
    id_to_group = {g.id: g for g in groups}
    for position, group_id in enumerate(requested):
        id_to_group[group_id].position = position
    db.session.commit()
    ordered = [id_to_group[group_id] for group_id in requested]
    return {"groups": _serialize_groups(ordered)}


def set_active_group(group_id: str, user_id: str | None = None) -> dict:
    """Persist the user's currently selected group.

    Args:
        group_id: Identifier of the group to mark active.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the active group identifier.

    Raises:
        ValueError: If the group is not found for the provided scope.
    """

    scope = _resolve_scope(user_id)
    group = _get_group(group_id, user_id=scope)
    preference = _ensure_preference(scope, [group])
    preference.active_group_id = group.id
    db.session.commit()
    return {"active_group_id": group.id}


def add_account_to_group(
    group_id: str,
    account_id: str,
    user_id: str | None = None,
) -> dict:
    """Attach an account to a group ensuring limits and uniqueness.

    Args:
        group_id: Identifier of the group receiving the account.
        account_id: Identifier of the account being added.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the updated group.

    Raises:
        ValueError: If the group or account cannot be found, the account
            already exists in the group, or the group is at capacity.
    """

    group = _get_group(group_id, user_id=user_id)
    account = _get_account(account_id)
    existing = (
        AccountGroupMembership.query.filter_by(group_id=group.id)
        .order_by(AccountGroupMembership.position.asc())
        .all()
    )
    if any(m.account_id == account.account_id for m in existing):
        raise ValueError("Account already in group")
    if len(existing) >= MAX_ACCOUNTS_PER_GROUP:
        raise ValueError("Maximum accounts per group reached")
    membership = AccountGroupMembership(
        group_id=group.id,
        account_id=account.account_id,
        position=len(existing),
    )
    db.session.add(membership)
    db.session.commit()
    return {"group": _serialize_groups([group])[0]}


def remove_account_from_group(
    group_id: str,
    account_id: str,
    user_id: str | None = None,
) -> dict:
    """Detach an account from a group.

    Args:
        group_id: Identifier of the group whose membership is updated.
        account_id: Identifier of the account to remove.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the refreshed group representation.

    Raises:
        ValueError: If the membership cannot be found for the group.
    """

    group = _get_group(group_id, user_id=user_id)
    membership = AccountGroupMembership.query.filter_by(
        group_id=group.id, account_id=account_id
    ).first()
    if not membership:
        raise ValueError("Account not found in group")
    db.session.delete(membership)
    db.session.flush()
    remaining = (
        AccountGroupMembership.query.filter_by(group_id=group.id)
        .order_by(
            AccountGroupMembership.position.asc(), AccountGroupMembership.id.asc()
        )
        .all()
    )
    for position, member in enumerate(remaining):
        member.position = position
    db.session.commit()
    return {"group": _serialize_groups([group])[0]}


def reorder_group_accounts(
    group_id: str,
    account_ids: Sequence[str],
    user_id: str | None = None,
) -> dict:
    """Update the ordering of accounts within a group.

    Args:
        group_id: Identifier of the group whose accounts are being ordered.
        account_ids: Sequence of account identifiers in the desired order.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        dict: Payload containing the updated group.

    Raises:
        ValueError: If the supplied IDs do not match the current membership.
    """

    group = _get_group(group_id, user_id=user_id)
    memberships = (
        AccountGroupMembership.query.filter_by(group_id=group.id)
        .order_by(
            AccountGroupMembership.position.asc(), AccountGroupMembership.id.asc()
        )
        .all()
    )
    existing_ids = {m.account_id for m in memberships}
    requested = [str(a) for a in account_ids]
    if existing_ids != set(requested):
        raise ValueError("Account list does not match group membership")
    id_to_membership = {m.account_id: m for m in memberships}
    for position, account_id in enumerate(requested):
        id_to_membership[account_id].position = position
    db.session.commit()
    return {"group": _serialize_groups([group])[0]}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_scope(user_id: str | None) -> str:
    """Normalize the provided user identifier.

    Args:
        user_id: Optional identifier from the request.

    Returns:
        str: A normalized identifier falling back to the default scope.
    """

    return (user_id or "").strip() or DEFAULT_USER_SCOPE


def _load_groups(user_id: str) -> list[AccountGroup]:
    """Load groups for the provided scope, creating a default when missing.

    Args:
        user_id: Identifier for which groups should be retrieved.

    Returns:
        list[AccountGroup]: Persisted group models ordered for display.
    """

    groups = (
        AccountGroup.query.filter_by(user_id=user_id)
        .order_by(AccountGroup.position.asc(), AccountGroup.created_at.asc())
        .all()
    )
    if groups:
        return groups
    default_group = AccountGroup(
        user_id=user_id,
        name=DEFAULT_GROUP_NAME,
        position=0,
        accent=DEFAULT_ACCENT,
    )
    db.session.add(default_group)
    db.session.commit()
    return [default_group]


def _ensure_preference(
    user_id: str, groups: Sequence[AccountGroup]
) -> AccountGroupPreference:
    """Ensure a preference record exists for the scope.

    Args:
        user_id: Identifier whose preference is being managed.
        groups: Iterable of groups considered valid.

    Returns:
        AccountGroupPreference: The existing or newly created preference.
    """

    preference = AccountGroupPreference.query.filter_by(user_id=user_id).first()
    valid_ids = {g.id for g in groups}
    if not preference:
        active_id = next(iter(valid_ids), None)
        preference = AccountGroupPreference(
            user_id=user_id,
            active_group_id=active_id,
        )
        db.session.add(preference)
        db.session.commit()
        return preference
    if preference.active_group_id not in valid_ids:
        preference.active_group_id = next(iter(valid_ids), None)
        db.session.commit()
    return preference


def _serialize_groups(groups: Sequence[AccountGroup]) -> list[dict]:
    """Serialize groups and memberships into a transport-friendly structure.

    Args:
        groups: Iterable of group models to serialize.

    Returns:
        list[dict]: Serialized representations for API responses.
    """

    if not groups:
        return []
    group_ids = [g.id for g in groups]
    memberships = (
        AccountGroupMembership.query.filter(
            AccountGroupMembership.group_id.in_(group_ids)
        )
        .order_by(
            AccountGroupMembership.group_id.asc(),
            AccountGroupMembership.position.asc(),
            AccountGroupMembership.id.asc(),
        )
        .all()
    )
    account_ids = {m.account_id for m in memberships}
    accounts = []
    if account_ids:
        accounts = (
            Account.query.filter(Account.account_id.in_(account_ids))
            .order_by(Account.account_id.asc())
            .all()
        )
    account_map = {acc.account_id: acc for acc in accounts}
    grouped: dict[str, list[AccountGroupMembership]] = {gid: [] for gid in group_ids}
    stale: list[AccountGroupMembership] = []
    for membership in memberships:
        if membership.account_id not in account_map:
            stale.append(membership)
            continue
        grouped[membership.group_id].append(membership)
    if stale:
        for membership in stale:
            db.session.delete(membership)
        db.session.commit()
    serialized: list[dict] = []
    for group in groups:
        serialized.append(
            {
                "id": group.id,
                "name": group.name,
                "accent": group.accent or DEFAULT_ACCENT,
                "position": group.position,
                "accounts": [
                    _serialize_account(account_map[m.account_id])
                    for m in grouped.get(group.id, [])
                ],
            }
        )
    return serialized


def _serialize_account(account: Account) -> dict:
    """Serialize an account model for dashboard consumption.

    Args:
        account: Account model instance to serialize.

    Returns:
        dict: Account payload with normalized balances.
    """

    balance = normalize_account_balance(account.balance, account.type)
    last_refreshed = None
    plaid_account = getattr(account, "plaid_account", None)
    if getattr(plaid_account, "last_refreshed", None):
        last_refreshed = _isoformat(plaid_account.last_refreshed)
    return {
        "id": account.account_id or str(account.id),
        "account_id": account.account_id,
        "name": account.name,
        "institution_name": account.institution_name,
        "type": account.type,
        "subtype": account.subtype,
        "link_type": account.link_type,
        "adjusted_balance": balance,
        "balance": balance,
        "is_hidden": account.is_hidden,
        "last_refreshed": last_refreshed,
    }


def _get_group(group_id: str, user_id: str | None = None) -> AccountGroup:
    """Fetch a group by identifier within an optional scope.

    Args:
        group_id: Identifier for the group to load.
        user_id: Optional identifier used to scope the lookup.

    Returns:
        AccountGroup: The resolved group model.

    Raises:
        ValueError: If the group does not exist within the scope.
    """

    scope = _resolve_scope(user_id)
    group = AccountGroup.query.filter_by(id=group_id, user_id=scope).first()
    if not group:
        raise ValueError("Group not found")
    return group


def _get_account(account_id: str) -> Account:
    """Fetch an account by identifier.

    Args:
        account_id: Identifier of the account to load.

    Returns:
        Account: The resolved account model.

    Raises:
        ValueError: If the account cannot be found.
    """

    account = Account.query.filter_by(account_id=str(account_id)).first()
    if not account:
        raise ValueError("Account not found")
    return account


def _resequence_groups(groups: Sequence[AccountGroup]) -> None:
    """Ensure groups have contiguous position values.

    Args:
        groups: Iterable of groups whose positions require normalization.
    """

    for position, group in enumerate(groups):
        group.position = position


def _isoformat(value) -> str | None:
    """Convert datetime-like values to ISO formatted strings.

    Args:
        value: A datetime instance or similar value.

    Returns:
        str | None: ISO formatted string or ``None`` when unavailable.
    """

    if not value:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
