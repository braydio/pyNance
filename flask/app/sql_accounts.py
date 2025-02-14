# sql_accounts.py
from config import logger
from db_models import AccountDetails, SessionLocal
from sqlalchemy.orm import joinedload

from flask import Blueprint, jsonify, render_template

accounts = Blueprint("accounts", __name__)


@accounts.route("/get_accounts", methods=["GET"])
def get_accounts():
    session = SessionLocal()
    try:
        # Query all accounts and eagerly load the associated institution
        accounts_list = (
            session.query(AccountDetails)
            .options(joinedload(AccountDetails.institution))
            .all()
        )
        result = []
        for account in accounts_list:
            result.append(
                {
                    "id": account.id,
                    "account_name": account.account_name,
                    "type": account.type,
                    "subtype": account.subtype,
                    "available_balance": account.available_balance,
                    "current_balance": account.current_balance,
                    "masked_access_token": account.masked_access_token,
                    "institution": account.institution.name
                    if account.institution
                    else None,
                }
            )
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()


@accounts.route("/accounts", methods=["GET"])
def accounts_page():
    session = SessionLocal()
    try:
        # Retrieve accounts along with institution details for the template
        accounts_list = (
            session.query(AccountDetails)
            .options(joinedload(AccountDetails.institution))
            .all()
        )
        data = []
        for account in accounts_list:
            data.append(
                {
                    "id": account.id,
                    "account_name": account.account_name,
                    "institution_name": account.institution.name
                    if account.institution
                    else "Unknown",
                    "type": account.type,
                    "subtype": account.subtype,
                    "balances": {
                        "available": account.available_balance,
                        "current": account.current_balance,
                    },
                }
            )
        return render_template("accounts.html", accounts=data)
    except Exception as e:
        logger.error(f"Error loading accounts page: {e}", exc_info=True)
        return render_template("error.html", error="Failed to load accounts data.")
    finally:
        session.close()
