"""Plaid webhooks endpoint for transactions and investments notifications."""

from collections import Counter as MemoryCounter
from datetime import date, datetime, timedelta, timezone
from typing import Tuple

from app.config import logger
from app.extensions import db
from app.helpers.plaid_helpers import get_investment_transactions
from app.models import PlaidAccount, PlaidWebhookLog
from app.services.plaid_sync import sync_account_transactions
from app.sql import investments_logic
from flask import Blueprint, jsonify, request

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter as PrometheusCounter
except Exception:  # pragma: no cover
    PrometheusCounter = None  # type: ignore[assignment]

PROM_COUNTER_NAME = "plaid_webhook_events_total"
PROM_COUNTER_HELP = "Total Plaid webhook outcomes by status and code"


def _build_prometheus_counter() -> "PrometheusCounter | None":
    """Create or retrieve the Prometheus counter for webhook outcomes."""

    if PrometheusCounter is None:  # Dependency not installed
        return None

    try:
        return PrometheusCounter(
            PROM_COUNTER_NAME, PROM_COUNTER_HELP, ["status", "code"]
        )
    except ValueError:  # pragma: no cover - already registered
        try:
            from prometheus_client import REGISTRY  # type: ignore

            return REGISTRY._names_to_collectors.get(PROM_COUNTER_NAME)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - registry internals changed
            return None


PROM_COUNTER = _build_prometheus_counter()


class WebhookMetrics:
    """Track webhook outcomes and optionally publish Prometheus counters."""

    def __init__(self) -> None:
        self._counts: MemoryCounter[Tuple[str, str]] = MemoryCounter()

    def increment(self, status: str, code: str | None, amount: int = 1) -> None:
        """Record a webhook result for observability.

        Args:
            status: Outcome label such as ``"success"`` or ``"failure"``.
            code: Plaid webhook code associated with the outcome.
            amount: Number of results represented by this increment.
        """

        if amount <= 0:
            return

        normalized = (code or "unknown").upper()
        self._counts[(status, normalized)] += amount
        if PROM_COUNTER is not None:
            PROM_COUNTER.labels(status=status, code=normalized).inc(amount)

    def count(self, status: str, code: str | None) -> int:
        """Return the stored count for a status/code pair."""

        normalized = (code or "unknown").upper()
        return int(self._counts.get((status, normalized), 0))

    def reset(self) -> None:
        """Clear in-memory metrics (useful for unit tests)."""

        self._counts.clear()


webhook_metrics = WebhookMetrics()

plaid_webhooks = Blueprint("plaid_webhooks", __name__)


@plaid_webhooks.route("/plaid", methods=["POST"])
def handle_plaid_webhook():
    """Process Plaid webhook payloads and dispatch downstream sync tasks."""

    payload = request.get_json(silent=True) or {}
    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")
    item_id = payload.get("item_id")

    # Persist webhook log for observability
    try:
        log = PlaidWebhookLog(
            event_type=f"{webhook_type}:{webhook_code}",
            webhook_type=webhook_type,
            webhook_code=webhook_code,
            item_id=item_id,
            payload=payload,
            received_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"Failed to store Plaid webhook log: {e}")

    # Banking transactions delta webhook
    if webhook_type == "TRANSACTIONS" and webhook_code in (
        "SYNC_UPDATES_AVAILABLE",
        "DEFAULT_UPDATE",
    ):
        if not item_id:
            logger.warning("Plaid webhook missing item_id; cannot dispatch sync")
            webhook_metrics.increment("failure", webhook_code)
            return jsonify({"status": "ignored"}), 200

        # Trigger sync for each account under this item
        accounts = PlaidAccount.query.filter_by(item_id=item_id).all()
        if not accounts:
            logger.info(
                "Plaid webhook %s:%s had no matching accounts for item %s",
                webhook_type,
                webhook_code,
                item_id,
            )
            webhook_metrics.increment("failure", webhook_code)
            return jsonify({"status": "ignored", "triggered": []}), 200

        triggered = []
        success_count = 0
        failure_count = 0
        for pa in accounts:
            try:
                res = sync_account_transactions(pa.account_id)
                triggered.append(res.get("account_id") or pa.account_id)
                success_count += 1
                webhook_metrics.increment("success", webhook_code)
            except Exception as e:
                logger.error(f"Sync failed for account {pa.account_id}: {e}")
                failure_count += 1
                webhook_metrics.increment("failure", webhook_code)

        logger.info(
            ("Plaid webhook %s:%s processed for item %s (success=%d, failure=%d)"),
            webhook_type,
            webhook_code,
            item_id,
            success_count,
            failure_count,
        )
        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Investments transactions webhook
    if webhook_type == "INVESTMENTS_TRANSACTIONS" and webhook_code in (
        "DEFAULT_UPDATE",
        "HISTORICAL_UPDATE",
    ):
        if not item_id:
            logger.warning(
                "Investments webhook missing item_id; cannot dispatch refresh"
            )
            return jsonify({"status": "ignored"}), 200

        # Determine a safe fetch window (last 30 days)
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()

        accounts = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).all()
        triggered = []
        for pa in accounts:
            try:
                txs = get_investment_transactions(pa.access_token, start_date, end_date)
                count = investments_logic.upsert_investment_transactions(txs)
                triggered.append({"account_id": pa.account_id, "investment_txs": count})
            except Exception as e:
                logger.error(
                    f"Investments tx refresh failed for account {pa.account_id}: {e}"
                )
        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Holdings price/position changes webhook
    if webhook_type == "HOLDINGS" and webhook_code in ("DEFAULT_UPDATE",):
        if not item_id:
            logger.warning("Holdings webhook missing item_id; cannot dispatch refresh")
            return jsonify({"status": "ignored"}), 200

        accounts = PlaidAccount.query.filter_by(
            item_id=item_id, product="investments"
        ).all()
        triggered = []
        for pa in accounts:
            try:
                sums = investments_logic.upsert_investments_from_plaid(
                    pa.account.user_id if pa.account else None, pa.access_token
                )
                triggered.append({"account_id": pa.account_id, **sums})
            except Exception as e:
                logger.error(
                    f"Investments holdings refresh failed for account {pa.account_id}: {e}"
                )
        return jsonify({"status": "ok", "triggered": triggered}), 200

    # Other webhook types
    return jsonify({"status": "ignored"}), 200
