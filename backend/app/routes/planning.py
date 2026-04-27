"""REST API routes for SQL-backed financial planning."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest

from app.services import planning_service

planning = Blueprint("planning", __name__)


def _json_body() -> dict | list:
    body = request.get_json(silent=True)
    if body is None:
        raise BadRequest("JSON body required")
    return body


@planning.get("/scenarios")
def list_scenarios():
    return jsonify(planning_service.list_scenarios())


@planning.post("/scenarios")
def create_scenario():
    body = _json_body()
    if not isinstance(body, dict):
        raise BadRequest("JSON object required")
    return jsonify(planning_service.create_scenario(body)), 201


@planning.get("/bills")
def list_bills():
    return jsonify(planning_service.get_bills())


@planning.post("/bills")
def create_bill():
    body = _json_body()
    if not isinstance(body, dict):
        raise BadRequest("JSON object required")
    return jsonify(planning_service.create_bill(body)), 201


@planning.put("/bills/<bill_id>")
def update_bill(bill_id: str):
    body = _json_body()
    if not isinstance(body, dict):
        raise BadRequest("JSON object required")
    return jsonify(planning_service.update_bill(bill_id, body))


@planning.delete("/bills/<bill_id>")
def delete_bill(bill_id: str):
    planning_service.delete_bill(bill_id)
    return jsonify({"status": "deleted"})


@planning.get("/scenarios/<scenario_id>/allocations")
def list_allocations(scenario_id: str):
    return jsonify(planning_service.get_allocations(scenario_id))


@planning.post("/scenarios/<scenario_id>/allocations")
def create_allocation(scenario_id: str):
    body = _json_body()
    if not isinstance(body, dict):
        raise BadRequest("JSON object required")
    return jsonify(planning_service.create_allocation(scenario_id, body)), 201


@planning.put("/scenarios/<scenario_id>/allocations/<allocation_id>")
def update_allocation(scenario_id: str, allocation_id: str):
    body = _json_body()
    if not isinstance(body, dict):
        raise BadRequest("JSON object required")
    return jsonify(planning_service.update_allocation(scenario_id, allocation_id, body))


@planning.delete("/scenarios/<scenario_id>/allocations/<allocation_id>")
def delete_allocation(scenario_id: str, allocation_id: str):
    planning_service.delete_allocation(scenario_id, allocation_id)
    return jsonify({"status": "deleted"})


@planning.put("/scenarios/<scenario_id>/allocations")
def replace_allocations(scenario_id: str):
    body = _json_body()
    if not isinstance(body, list):
        raise BadRequest("JSON array required")
    return jsonify(planning_service.replace_allocations(scenario_id, body))


__all__ = ["planning"]
