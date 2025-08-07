from app.services.fidelity_service import FidelityService
from flask import Blueprint, jsonify

bp = Blueprint("fidelity", __name__)


@bp.route("/fidelity/investments", methods=["GET"])
def get_fidelity_investments():
    service = FidelityService()
    accounts = service.get_investment_accounts()
    return jsonify(accounts)
