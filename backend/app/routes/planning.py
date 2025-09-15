"""REST API routes for financial planning.

This module exposes endpoints for managing planned bills and
allocation targets. The actual data access is delegated to the
``planning_service`` module which is patched in tests and can be
implemented separately. Each view function returns JSON responses and
performs minimal request validation.
"""

from __future__ import annotations

from app.services import planning_service
from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

# Blueprint for planning routes
planning = Blueprint("planning", __name__)


@planning.get("/bills")
def list_bills():
    """Return all planned bills.

    Returns:
        flask.Response: JSON list of bill dictionaries.
    """

    bills = planning_service.get_bills()
    return jsonify(bills)


@planning.post("/bills")
def create_bill():
    """Create a new planned bill.

    Expects a JSON body representing the bill fields which will be
    forwarded to :func:`planning_service.create_bill`.

    Returns:
        flask.Response: JSON representation of the created bill with a
        ``201`` status code.
    """

    body = request.get_json(silent=True)
    if body is None:
        raise BadRequest("JSON body required")
    bill = planning_service.create_bill(body)
    return jsonify(bill), 201


@planning.put("/bills/<bill_id>")
def update_bill(bill_id: str):
    """Update an existing bill.

    Args:
        bill_id: Identifier of the bill to update.

    Returns:
        flask.Response: JSON representation of the updated bill.
    """

    body = request.get_json(silent=True)
    if body is None:
        raise BadRequest("JSON body required")
    bill = planning_service.update_bill(bill_id, body)
    return jsonify(bill)


@planning.delete("/bills/<bill_id>")
def delete_bill(bill_id: str):
    """Delete a bill by identifier.

    Args:
        bill_id: Identifier of the bill to delete.

    Returns:
        flask.Response: JSON confirmation of deletion.
    """

    planning_service.delete_bill(bill_id)
    return jsonify({"status": "deleted"})


@planning.get("/allocations")
def list_allocations():
    """Return allocation targets for the planning scenario.

    Returns:
        flask.Response: JSON list of allocation dictionaries.
    """

    allocations = planning_service.get_allocations()
    return jsonify(allocations)


@planning.put("/allocations")
def update_allocations():
    """Replace allocation targets.

    The JSON body is forwarded to
    :func:`planning_service.update_allocations` which returns the
    updated allocation list.

    Returns:
        flask.Response: JSON list of updated allocations.
    """

    body = request.get_json(silent=True)
    if body is None:
        raise BadRequest("JSON body required")
    allocations = planning_service.update_allocations(body)
    return jsonify(allocations)


__all__ = ["planning"]
