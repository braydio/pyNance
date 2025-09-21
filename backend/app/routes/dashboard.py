"""Dashboard-specific API routes."""

from app.config import logger
from app.services import account_groups as account_group_service
from app.services.account_snapshot import (
    DEFAULT_USER_SCOPE,
    build_snapshot_payload,
    update_snapshot_selection,
)
from flask import Blueprint, jsonify, request

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/account_snapshot", methods=["GET"])
def get_account_snapshot():
    """Return stored snapshot preferences and hydrated account data."""
    user_id = request.args.get("user_id") or DEFAULT_USER_SCOPE
    try:
        data = build_snapshot_payload(user_id=user_id)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to load account snapshot preferences: %s", exc, exc_info=True
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account_snapshot", methods=["PUT"])
def update_account_snapshot():
    """Persist a new snapshot selection."""
    payload = request.get_json(silent=True) or {}
    user_id = (
        payload.get("user_id") or request.args.get("user_id") or DEFAULT_USER_SCOPE
    )
    selected_ids = payload.get("selected_account_ids")

    if selected_ids is None:
        return (
            jsonify({"status": "error", "message": "selected_account_ids is required"}),
            400,
        )
    if not isinstance(selected_ids, list):
        return (
            jsonify(
                {"status": "error", "message": "selected_account_ids must be a list"}
            ),
            400,
        )

    try:
        data = update_snapshot_selection(selected_ids, user_id=user_id)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to update account snapshot preferences: %s", exc, exc_info=True
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


def _group_scope(payload: dict | None = None) -> str:
    """Resolve the user scope for account group requests.

    Args:
        payload: Optional JSON payload supplied with the request.

    Returns:
        str: Identifier representing the user scope.
    """

    payload = payload or {}
    return (
        payload.get("user_id")
        or request.args.get("user_id")
        or account_group_service.DEFAULT_USER_SCOPE
    )


@dashboard.route("/account-groups", methods=["GET"])
def get_account_groups():
    """Return persisted account groups for the requesting user.

    Returns:
        Response: JSON API response wrapping the account group payload.
    """

    user_id = request.args.get("user_id")
    try:
        data = account_group_service.list_account_groups(user_id=user_id)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to load account groups: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups", methods=["POST"])
def create_account_group():
    """Create a new account group.

    Returns:
        Response: JSON API response containing the created group payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    try:
        data = account_group_service.create_account_group(
            name=payload.get("name"),
            accent=payload.get("accent"),
            group_id=payload.get("id"),
            user_id=scope,
        )
        return jsonify({"status": "success", "data": data}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to create account group: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/<group_id>", methods=["PUT"])
def update_account_group(group_id: str):
    """Update group metadata such as the display name.

    Args:
        group_id: Identifier of the group to update.

    Returns:
        Response: JSON API response containing the updated group payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    try:
        data = account_group_service.update_account_group(
            group_id,
            user_id=scope,
            name=payload.get("name"),
            accent=payload.get("accent"),
        )
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to update account group %s: %s", group_id, exc, exc_info=True
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/<group_id>", methods=["DELETE"])
def delete_account_group(group_id: str):
    """Delete an account group for the current user.

    Args:
        group_id: Identifier of the group to delete.

    Returns:
        Response: JSON API response with the remaining groups payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    try:
        data = account_group_service.delete_account_group(group_id, user_id=scope)
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to delete account group %s: %s", group_id, exc, exc_info=True
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/reorder", methods=["POST"])
def reorder_account_groups():
    """Persist a new order for all account groups.

    Returns:
        Response: JSON API response containing the reordered groups payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    group_ids = payload.get("group_ids")
    if not isinstance(group_ids, list) or not group_ids:
        return (
            jsonify(
                {"status": "error", "message": "group_ids must be a non-empty list"}
            ),
            400,
        )
    try:
        data = account_group_service.reorder_account_groups(group_ids, user_id=scope)
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to reorder account groups: %s", exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/active", methods=["PUT"])
def set_active_account_group():
    """Update the active group selection for the user.

    Returns:
        Response: JSON API response containing the active group ID payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    group_id = payload.get("group_id")
    if not group_id:
        return (
            jsonify({"status": "error", "message": "group_id is required"}),
            400,
        )
    try:
        data = account_group_service.set_active_group(group_id, user_id=scope)
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to set active group %s: %s", group_id, exc, exc_info=True)
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/<group_id>/accounts", methods=["POST"])
def add_account_to_group(group_id: str):
    """Attach an account to a group.

    Args:
        group_id: Identifier of the group receiving the account.

    Returns:
        Response: JSON API response containing the updated group payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    account_id = payload.get("account_id")
    if not account_id:
        return (
            jsonify({"status": "error", "message": "account_id is required"}),
            400,
        )
    try:
        data = account_group_service.add_account_to_group(
            group_id, account_id, user_id=scope
        )
        return jsonify({"status": "success", "data": data}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to add account %s to group %s: %s",
            account_id,
            group_id,
            exc,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/<group_id>/accounts/<account_id>", methods=["DELETE"])
def remove_account_from_group(group_id: str, account_id: str):
    """Remove an account from a group.

    Args:
        group_id: Identifier of the group being modified.
        account_id: Identifier of the account to remove from the group.

    Returns:
        Response: JSON API response containing the updated group payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    try:
        data = account_group_service.remove_account_from_group(
            group_id, account_id, user_id=scope
        )
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 404
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to remove account %s from group %s: %s",
            account_id,
            group_id,
            exc,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(exc)}), 500


@dashboard.route("/account-groups/<group_id>/accounts/reorder", methods=["POST"])
def reorder_group_accounts(group_id: str):
    """Persist ordering changes for accounts within a group.

    Args:
        group_id: Identifier of the group whose accounts are being reordered.

    Returns:
        Response: JSON API response containing the updated group payload.
    """

    payload = request.get_json(silent=True) or {}
    scope = _group_scope(payload)
    account_ids = payload.get("account_ids")
    if not isinstance(account_ids, list) or not account_ids:
        return (
            jsonify(
                {"status": "error", "message": "account_ids must be a non-empty list"}
            ),
            400,
        )
    try:
        data = account_group_service.reorder_group_accounts(
            group_id, account_ids, user_id=scope
        )
        return jsonify({"status": "success", "data": data}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to reorder accounts for group %s: %s", group_id, exc, exc_info=True
        )
        return jsonify({"status": "error", "message": str(exc)}), 500
