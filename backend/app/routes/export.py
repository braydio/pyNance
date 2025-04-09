
# backend/app/routes/export.py
from flask import Blueprint, jsonify
from app.sql.export_logic import export_csv_response, export_all_to_csv

export = Blueprint("export", __name__)

@export.route("/<model_name>", methods=["GET"])
def export_model_csv(model_name):
    try:
        response = export_csv_response(model_name)
        if response is None:
            return jsonify({"status": "error", "message": f"Unknown model '{model_name}'"}), 404
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@export.route("/all", methods=["GET"])
def export_all_models():
    try:
        export_all_to_csv()
        return jsonify({"status": "success", "message": "All models exported to local CSV files."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

