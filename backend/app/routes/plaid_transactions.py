# file: app/routes/plaid_transactions.py
"""Endpoints for Plaid account linking and transaction sync."""

from datetime import datetime
from typing import Optional

from app.config import CLIENT_NAME, PLAID_CLIENT_ID, logger, plaid_client
from app.extensions import db
from app.helpers.plaid_helpers import (
    exchange_public_token,
    generate_link_token,
    get_accounts,
    get_institution_name,
    get_item,
    remove_item,
)
from app.models import Account, PlaidAccount, PlaidItem
from app.sql import account_logic  # for upserting accounts and processing transactions
from flask import Blueprint, jsonify, request
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from sqlalchemy.orm import joinedload

plaid_transactions = Blueprint("plaid_transactions", __name__)


def resolve_account_by_any_id(identifier) -> Optional[Account]:
    """
    Resolve account by either numeric primary key or external account_id.

    Args:
        identifier: Either integer ID, string numeric ID, or external account_id

    Returns:
        Account object if found, None otherwise
    """
    # If identifier is numeric-like, try primary key first
    try:
        if isinstance(identifier, int) or (
            isinstance(identifier, str) and identifier.isdigit()
        ):
            acct = Account.query.get(int(identifier))
            if acct:
                return acct
    except Exception:
        pass

    # Fallback to external string account_id
    try:
        return Account.query.filter_by(account_id=str(identifier)).first()
    except Exception:
        return None


@plaid_transactions.route("/generate_link_token", methods=["POST"])
def generate_link_token_endpoint():
    data = request.get_json()
    user_id = data.get("user_id", PLAID_CLIENT_ID)
    products = data.get("products", ["transactions"])
    try:
        logger.debug(
            "Request to generate link token with user_id=%s, products=%s",
            user_id,
            products,
        )
        token = generate_link_token(products=products, user_id=user_id)
        if not token:
            logger.warning("Failed to generate link token - token was None")
            return (
                jsonify(
                    {"status": "error", "message": "Failed to generate link token"}
                ),
                500,
            )
        logger.info("Generated link token for user_id=%s", user_id)
        return jsonify({"status": "success", "link_token": token}), 200
    except Exception as e:
        logger.error("Error generating link token: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/exchange_public_token", methods=["POST"])
def exchange_public_token_endpoint():
    data = request.get_json()
    frontend_user_id = data.get("user_id", "")
    user_id = frontend_user_id or CLIENT_NAME

    if not user_id:
        logger.error("No user_id available from frontend or env")
        return jsonify({"error": "user_id is required"}), 400

    logger.debug(
        "user_id resolved from %s: %s",
        "frontend" if frontend_user_id else "env",
        user_id,
    )

    public_token = data.get("public_token")
    logger.debug("Received token exchange request for user_id=%s", user_id)

    if not user_id or not public_token:
        logger.warning("Missing user_id or public_token in request")
        return jsonify({"error": "Missing user_id or public_token"}), 400

    try:
        exchange_resp = exchange_public_token(public_token)
        logger.debug("Exchange response item_id=%s", exchange_resp.get("item_id"))
        if not exchange_resp:
            logger.warning("Exchange returned no response")
            return jsonify({"error": "Token exchange failed"}), 500

        access_token = exchange_resp.get("access_token")
        item_id = exchange_resp.get("item_id")
        logger.info(
            "Token exchange successful. Access Token: %s, Item ID: %s",
            access_token,
            item_id,
        )

        if not access_token or not item_id:
            logger.error("Missing access_token or item_id after exchange")
            return jsonify({"error": "Failed to exchange public token"}), 500

        item_info = get_item(access_token)
        institution_id = item_info.get("institution_id", "Unknown")
        institution_name = get_institution_name(institution_id)
        logger.debug("Institution ID: %s, Name: %s", institution_id, institution_name)

        accounts = get_accounts(access_token, user_id)
        logger.debug("Retrieved %d accounts from Plaid", len(accounts))

        # --- Persist 1 row per Item in secure table ---
        try:
            product = (data.get("product") or "transactions").strip() or "transactions"
            existing_item = PlaidItem.query.filter_by(item_id=item_id).first()
            if existing_item:
                existing_item.access_token = access_token
                existing_item.user_id = str(user_id)
                existing_item.institution_name = institution_name
                existing_item.product = product
                existing_item.is_active = True
            else:
                db.session.add(
                    PlaidItem(
                        user_id=str(user_id),
                        item_id=item_id,
                        access_token=access_token,
                        institution_name=institution_name,
                        product=product,
                        is_active=True,
                    )
                )
            logger.debug(
                "Upserted PlaidItem for item_id=%s (product=%s)",
                item_id,
                product,
            )
        except Exception as e:
            logger.error("Failed to upsert PlaidItem: %s", e)

        # --- PATCH: Persist PlaidAccount entries ---
        for acct in accounts:
            account_id = acct.get("account_id")
            if not account_id:
                continue

            exists = PlaidAccount.query.filter_by(account_id=account_id).first()
            if exists:
                logger.debug("PlaidAccount already exists for %s", account_id)
                continue

            new_plaid_account = PlaidAccount(
                account_id=account_id,
                access_token=access_token,
                item_id=item_id,
                institution_id=institution_id,
                # Store naive timestamp to match column type
                last_refreshed=datetime.now(),
            )
            db.session.add(new_plaid_account)

        for acct in accounts:
            acct["institution_name"] = institution_name
            logger.debug(
                "Injected institution name into %d accounts: %s",
                len(accounts),
                institution_name,
            )

        db.session.commit()

        logger.debug("[CHECK] Calling upsert_accounts() with user_id=%s", user_id)
        account_logic.upsert_accounts(
            user_id, accounts, provider="plaid", access_token=access_token
        )
        logger.info("Upserted %d accounts for user %s", len(accounts), user_id)

        return (
            jsonify(
                {
                    "status": "success",
                    "item_id": item_id,
                    "institution_name": institution_id,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Error exchanging public token: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/delete_account", methods=["DELETE"])
def delete_plaid_account():
    """Delete an account and revoke its Plaid item."""
    try:
        data = request.get_json(silent=True) or {}
        account_id = data.get("account_id")
        logger.debug("Received request to delete account_id=%s", account_id)

        if not account_id:
            logger.warning("No account_id provided in request")
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        plaid_acct = PlaidAccount.query.filter_by(account_id=account_id).first()
        if not plaid_acct:
            logger.warning("PlaidAccount not found for account_id=%s", account_id)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"No PlaidAccount found for {account_id}",
                    }
                ),
                404,
            )

        # Collect all accounts tied to the same Plaid item so we don't orphan them
        item_id = plaid_acct.item_id
        linked_accounts = [plaid_acct.account_id]
        if item_id:
            linked_accounts = [
                pa.account_id
                for pa in PlaidAccount.query.filter_by(item_id=item_id).all()
                if pa.account_id
            ]

        access_token = plaid_acct.access_token
        if not access_token and item_id:
            plaid_item = PlaidItem.query.filter_by(item_id=item_id).first()
            access_token = getattr(plaid_item, "access_token", None)

        plaid_acct = PlaidAccount.query.filter_by(account_id=account_id).first()
        if access_token:
            try:
                remove_item(access_token)
            except Exception as ex:
                logger.warning("Failed to remove Plaid item: %s", ex)

        if item_id:
            # Clean up the stored PlaidItem row for this item as well
            PlaidItem.query.filter_by(item_id=item_id).delete()

        deleted_count = Account.query.filter(
            Account.account_id.in_(linked_accounts)
        ).delete(synchronize_session=False)
        db.session.commit()
        logger.info(
            "Deleted Plaid item %s and %d linked account(s): %s",
            item_id or "<none>",
            deleted_count or 0,
            ", ".join(linked_accounts),
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "deleted_accounts": linked_accounts,
                    "item_id": item_id,
                }
            ),
            200,
        )
    except Exception as e:
        logger.error("Error deleting Plaid account: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@plaid_transactions.route("/refresh_accounts", methods=["POST"])
def refresh_accounts_endpoint():
    data = request.get_json()
    user_id = data.get("user_id")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")
    account_ids = data.get("account_ids") or []
    start_date = (
        datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
    )
    end_date = (
        datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    )
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        query = Account.query.options(joinedload(Account.plaid_account)).filter_by(
            user_id=user_id
        )
        if account_ids:
            query = query.filter(Account.account_id.in_(account_ids))
        accounts = query.all()
        refreshed = []
        token_account_cache: dict[str, list] = {}
        for acct in accounts:
            if acct.plaid_account and acct.plaid_account.access_token:
                access_token = acct.plaid_account.access_token
                accounts_data = token_account_cache.get(access_token)
                if accounts_data is None:
                    accounts_data = get_accounts(access_token, acct.user_id)
                    if accounts_data is None:
                        logger.warning(
                            "Plaid rate limit hit; skipping account %s", acct.account_id
                        )
                        continue
                    accounts_data = [
                        item.to_dict() if hasattr(item, "to_dict") else dict(item)
                        for item in accounts_data
                    ]
                    token_account_cache[access_token] = accounts_data
                refreshed_flag, _ = account_logic.refresh_data_for_plaid_account(
                    access_token=access_token,
                    account_or_id=acct,
                    accounts_data=accounts_data,
                    start_date=start_date,
                    end_date=end_date,
                )
                if refreshed_flag:
                    refreshed.append(
                        acct.name or acct.account_id
                    )  # ✅ return readable name
            else:
                logger.warning(
                    "Missing access token for account %s (user %s)",
                    acct.account_id,
                    user_id,
                )

        return jsonify({"status": "success", "updated_accounts": refreshed}), 200

    except Exception as e:
        logger.error("Error refreshing accounts: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@plaid_transactions.route("/generate_update_link_token", methods=["POST"])
def generate_update_link_token():
    """Generate a Plaid Link token in update mode to resolve ITEM_LOGIN_REQUIRED.

    This endpoint generates a Link token that can be used to re-authenticate
    a Plaid item when the user's credentials have changed.
    """
    try:
        data = request.get_json() or {}
        account_id = data.get("account_id")

        if not account_id:
            logger.warning("Missing account_id in update link token request")
            return (
                jsonify({"status": "error", "message": "Missing account_id parameter"}),
                400,
            )

        # Resolve account robustly (handles both numeric IDs and external account_ids)
        account = resolve_account_by_any_id(account_id)
        if not account:
            logger.warning("Account %s not found for update link token", account_id)
            return jsonify({"status": "error", "message": "Account not found"}), 404

        # Check if account has Plaid integration
        if not account.plaid_account or not account.plaid_account.access_token:
            logger.warning("Account %s missing Plaid access token", account.account_id)
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Account is not linked to Plaid or missing access token",
                    }
                ),
                400,
            )

        access_token = account.plaid_account.access_token
        logger.info(
            "Generating update link token for account %s (user %s)",
            account.account_id,
            account.user_id,
        )

        # Create Link token in update mode
        req = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id=str(account.user_id)),
            client_name="pyNance",
            language="en",
            country_codes=[CountryCode("US")],
            products=[Products("transactions")],
            access_token=access_token,  # This puts Link in update mode
        )

        response = plaid_client.link_token_create(req)

        logger.info(
            "Successfully generated update link token for account %s",
            account.account_id,
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "link_token": response.link_token,
                    "expiration": (
                        response.expiration.isoformat() if response.expiration else None
                    ),
                    "account_id": account.account_id,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error("Error generating update link token: %s", e, exc_info=True)

        # Check if it's a Plaid API error
        if hasattr(e, "body"):
            try:
                error_body = e.body
                logger.error("Plaid API error details: %s", error_body)
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Plaid API error",
                            "plaid_error": error_body,
                        }
                    ),
                    502,
                )
            except Exception:
                pass

        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to generate update link token: {str(e)}",
                }
            ),
            500,
        )


@plaid_transactions.route("/sync", methods=["POST"])
def sync_transactions_endpoint():
    """Trigger Plaid transactions/sync for a single account.

    Body: { "account_id": "..." }
    """
    try:
        data = request.get_json() or {}
        account_id = data.get("account_id")
        if not account_id:
            return jsonify({"status": "error", "message": "Missing account_id"}), 400

        plaid_account = (
            PlaidAccount.query.options(joinedload(PlaidAccount.account))
            .filter_by(account_id=account_id)
            .first()
        )
        if not plaid_account or not plaid_account.access_token:
            logger.warning(
                "Sync requested for unknown or unlinked Plaid account %s",
                account_id,
            )
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Plaid account not found or missing access token",
                    }
                ),
                404,
            )

        accounts_data = get_accounts(plaid_account.access_token, plaid_account.account.user_id)
        if accounts_data is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Plaid rate limit hit; try again later",
                        "code": "PLAID_RATE_LIMIT",
                    }
                ),
                429,
            )
        accounts_data = [
            item.to_dict() if hasattr(item, "to_dict") else dict(item) for item in accounts_data
        ]

        result = account_logic.refresh_data_for_plaid_account(
            plaid_account.access_token,
            plaid_account.account,
            accounts_data=accounts_data,
        )
        if isinstance(result, tuple) and len(result) == 2:
            updated, error = result
        else:
            updated, error = bool(result), None

        if error:
            logger.error(
                "Plaid refresh returned an error for %s: %s",
                plaid_account.account_id,
                error,
            )
            db.session.rollback()
            return (
                jsonify(
                    {
                        "status": "success",
                        "result": {"updated": updated, "error": error},
                    }
                ),
                200,
            )

        # Store naive timestamp to match column type
        timestamp = datetime.now()
        plaid_account.last_refreshed = timestamp
        if plaid_account.account:
            plaid_account.account.updated_at = timestamp

        try:
            db.session.commit()
        except Exception as commit_err:  # pragma: no cover - defensive
            db.session.rollback()
            logger.error(
                "Failed to persist Plaid sync metadata for account %s: %s",
                plaid_account.account_id,
                commit_err,
            )
            return (
                jsonify({"status": "error", "message": "Failed to update metadata"}),
                500,
            )

        return (
            jsonify(
                {"status": "success", "result": {"updated": updated, "error": None}}
            ),
            200,
        )
    except Exception as e:
        logger.error("Error during Plaid sync: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
