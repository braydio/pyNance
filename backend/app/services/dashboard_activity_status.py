"""Generate dashboard activity-status guidance from account and transaction context."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import requests
from sqlalchemy import or_

from app.config import logger
from app.extensions import db
from app.models import Account, Transaction

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
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
    start_date: datetime,
    end_date: datetime,
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
            "date": tx.date.date().isoformat(),
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
            "message": "No recent activity was found. Review linked accounts to make sure data is syncing.",
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


def _call_openai_for_status(payload: dict[str, Any]) -> dict[str, str]:
    """Request a single parseable status message from OpenAI."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    model = os.getenv("OPENAI_DASHBOARD_MODEL", DEFAULT_OPENAI_MODEL)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        OPENAI_API_URL,
        headers=headers,
        timeout=15,
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
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Generate dashboard activity status text for the greeting area.

    Args:
        start_date: Optional UTC datetime lower bound for transaction context.
        end_date: Optional UTC datetime upper bound for transaction context.
        user_id: Optional user scope identifier.

    Returns:
        Parseable response payload with a single guidance message and context metadata.
    """

    resolved_end = end_date or datetime.now(UTC)
    resolved_start = start_date or (resolved_end - timedelta(days=30))
    accounts = _load_accounts(user_id=user_id)
    transactions = _load_transactions(start_date=resolved_start, end_date=resolved_end, user_id=user_id)
    payload = {
        "range": {
            "start_date": resolved_start.date().isoformat(),
            "end_date": resolved_end.date().isoformat(),
        },
        "accounts": accounts,
        "transactions": transactions,
    }

    try:
        generated = _call_openai_for_status(payload)
        if generated.get("message"):
            return {**generated, "source": "llm"}
    except Exception as exc:  # pragma: no cover - network + provider fallback
        logger.warning("Falling back to deterministic activity status: %s", exc)

    return {**_build_fallback_message(accounts, transactions), "source": "fallback"}
