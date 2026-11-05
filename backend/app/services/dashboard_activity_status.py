"""Generate dashboard activity-status guidance from account and transaction context."""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import requests
from sqlalchemy import or_

from app.config import logger
from app.models import Account, Transaction
from app.services.llm_settings import _validate_base_url, get_llm_settings

DEFAULT_LOCAL_MODEL = "llama3.2"
MAX_ACCOUNTS_IN_PROMPT = 12
MAX_TRANSACTIONS_IN_PROMPT = 25


def _to_float(value: Decimal | int | float | None) -> float:
    """Safely convert numeric values to float for JSON serialization."""

    if value is None:
        return 0.0
    return float(value)


def _load_accounts(user_id: str | None = None) -> list[dict[str, Any]]:
    """Load visible accounts for dashboard activity context."""

    query = Account.query.filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
    if user_id:
        query = query.filter(Account.user_id == user_id)
    accounts = query.order_by(Account.balance.desc()).limit(MAX_ACCOUNTS_IN_PROMPT).all()
    return [
        {
            "account_id": account.account_id,
            "name": account.display_name,
            "type": account.account_type,
            "balance": _to_float(account.balance),
        }
        for account in accounts
    ]


def _load_transactions(
    start_date: date,
    end_date: date,
    user_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load recent transactions for dashboard activity context."""

    query = Transaction.query.filter(
        Transaction.date >= start_date,
        Transaction.date <= end_date,
        or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)),
    )
    if user_id:
        query = query.filter(Transaction.user_id == user_id)
    transactions = (
        query.order_by(Transaction.date.desc(), Transaction.transaction_id.desc())
        .limit(MAX_TRANSACTIONS_IN_PROMPT)
        .all()
    )
    return [
        {
            "transaction_id": tx.transaction_id,
            "date": tx.date.isoformat(),
            "description": tx.description or tx.merchant_name or "Unknown transaction",
            "amount": _to_float(tx.amount),
            "account_id": tx.account_id,
        }
        for tx in transactions
    ]


def _build_fallback_message(accounts: list[dict[str, Any]], transactions: list[dict[str, Any]]) -> dict[str, str]:
    """Build deterministic fallback guidance when the LLM is unavailable."""

    if not transactions:
        return {
            "status_key": "no_recent_activity",
            "message": "No recent activity found. Check linked accounts.",
        }

    largest_expense = min((tx for tx in transactions), key=lambda tx: tx["amount"], default=None)
    if largest_expense and largest_expense["amount"] < 0:
        amount = abs(largest_expense["amount"])
        return {
            "status_key": "largest_expense",
            "message": (
                f"Your largest recent expense was ${amount:,.2f}. "
                "Verify that this charge is expected and tag it if needed."
            ),
        }

    total_balance = sum(account["balance"] for account in accounts)
    return {
        "status_key": "balance_check",
        "message": f"Your visible accounts total ${total_balance:,.2f}. Confirm that this matches your expected cash position.",
    }


def _chat_completions_url(base_url: str | None) -> str:
    """Resolve an explicitly configured local model server endpoint."""

    cleaned = _validate_base_url(base_url)
    if not cleaned:
        raise ValueError("A local model server URL is required")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def _call_local_model_for_status(payload: dict[str, Any], base_url: str) -> dict[str, str]:
    """Request a status message from the configured local model server."""

    # Validate again at the transport boundary: persisted URLs may predate validation.
    url = _chat_completions_url(base_url)
    model = os.getenv("LOCAL_LLM_MODEL") or DEFAULT_LOCAL_MODEL
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        timeout=15,
        allow_redirects=False,
        json={
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a personal finance dashboard assistant. "
                        "Return strict JSON with keys: status_key, message. "
                        "The message must be one concise sentence with exactly one practical suggestion."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze this activity context and provide one useful suggestion:\n"
                        f"{json.dumps(payload, separators=(',', ':'))}"
                    ),
                },
            ],
        },
    )
    response.raise_for_status()
    body = response.json()
    raw_content = body["choices"][0]["message"]["content"]
    parsed = json.loads(raw_content)
    return {
        "status_key": str(parsed.get("status_key") or "activity_tip"),
        "message": str(parsed.get("message") or "").strip(),
    }


def generate_activity_status(
    start_date: date | None = None,
    end_date: date | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate dashboard activity status text for the greeting area.

    Args:
        start_date: Optional calendar-date lower bound for transaction context.
        end_date: Optional calendar-date upper bound for transaction context.
        user_id: Optional user scope identifier.

    Returns:
        Parseable response payload with a single guidance message and context metadata.
    """

    resolved_end = end_date or datetime.now(UTC).date()
    resolved_start = start_date or (resolved_end - timedelta(days=30))
    accounts = _load_accounts(user_id=user_id)
    transactions = _load_transactions(start_date=resolved_start, end_date=resolved_end, user_id=user_id)
    payload = {
        "range": {
            "start_date": resolved_start.isoformat(),
            "end_date": resolved_end.isoformat(),
        },
        "accounts": accounts,
        "transactions": transactions,
    }

    try:
        llm_settings = get_llm_settings()
        if not llm_settings.custom_message_enabled or not llm_settings.base_url:
            return {**_build_fallback_message(accounts, transactions), "source": "fallback"}
        generated = _call_local_model_for_status(payload, base_url=llm_settings.base_url)
        if generated.get("message"):
            return {**generated, "source": "llm"}
    except Exception as exc:  # pragma: no cover - network + provider fallback
        logger.warning("Falling back to deterministic activity status: %s", exc)

    return {**_build_fallback_message(accounts, transactions), "source": "fallback"}
