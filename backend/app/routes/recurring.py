# app/routes/recurring.py
import types
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.config import logger
from app.extensions import db
from app.models import Transaction

recurring = Blueprint("recurring", __name__)

# --------------------------------------
# Utility
# --------------------------------------


def add_months(original_date, months=1):
    new_month = original_date.month + months
    new_year = original_date.year
    while new_month > 12:
        new_month -= 12
        new_year += 1
    try:
        return original_date.replace(year=new_year, month=new_month)
    except ValueError:
        return original_date.replace(year=new_year, month=new_month, day=28)


def _build_auto_confidence_score(occurrences, latest_date, recent_cutoff, today):
    """Score auto-detected recurring confidence from history depth and recency.

    Args:
        occurrences (int): Number of matching transactions in the recent window.
        latest_date (date): Most recent observed transaction date for the pattern.
        recent_cutoff (date): Inclusive lower bound used for detection.
        today (date): Current day.

    Returns:
        int: Confidence score on a 0-100 scale.
    """
    occurrence_score = min(max(occurrences - 1, 0) * 15, 60)
    lookback_days = max((today - recent_cutoff).days, 1)
    recency_days = max((today - latest_date).days, 0)
    recency_ratio = max(0.0, 1 - (recency_days / lookback_days))
    recency_score = round(recency_ratio * 40)
    return max(0, min(100, occurrence_score + recency_score))


# --------------------------------------
# PUT /accounts/<account_id>/recurringTx
# Save or update a recurring transaction
# --------------------------------------


def _error_response(exc):
    """JSON error for a ``RecurringError`` using its own HTTP status."""
    return jsonify({"status": "error", "code": exc.code, "message": str(exc)}), exc.status


def _source_transaction_fields(owner_id, account_id, tx_id):
    """Return ``(description, canonical_delta)`` from an owner-scoped transaction or raise."""
    from app.services import recurring_repository as repo
    from app.services.transaction_semantics import normalize_amount

    tx = Transaction.query.filter_by(transaction_id=tx_id, account_id=account_id).first()
    if tx is None or (tx.user_id and tx.user_id != owner_id):
        raise repo.StreamNotFound("Transaction not found for this account")
    result = normalize_amount(provider=getattr(tx.provider, "value", tx.provider), raw_amount=tx.amount)
    if result.delta is None:
        raise repo.ValidationFailed("Transaction amount direction is unknown; enter the amount manually")
    name = tx.merchant_name if tx.merchant_name not in (None, "", "Unknown") else tx.description
    return name or "Recurring payment", result.delta


@recurring.route("/accounts/<account_id>/recurringTx", methods=["PUT"])
def update_recurring_tx(account_id):
    """Create or update a user-defined recurring plan (legacy shape, backed by recurring streams).

    ``amount`` is the signed cash amount (negative = money out). With ``tx_id`` the description and
    amount come from that owner-scoped transaction; otherwise ``description`` and ``amount`` are
    required. ``user_id`` in the payload is ignored: the owner is configured server-side.
    """
    from app.services import recurring_repository as repo

    try:
        owner_id = repo.trusted_owner_id()
        repo.owned_account(owner_id, account_id)
        data = request.get_json(silent=True) or {}
        tx_id = data.get("tx_id")
        if tx_id:
            description, amount = _source_transaction_fields(owner_id, account_id, tx_id)
        else:
            description = (data.get("description") or "").strip()
            if not description or data.get("amount") is None:
                raise repo.ValidationFailed("description and amount are required without tx_id")
            amount = data.get("amount")
        frequency = data.get("frequency", "monthly")
        next_due = data.get("next_due_date")
        anchor = repo.parse_date(next_due, "next_due_date") if next_due else date.today() + timedelta(days=30)
        notes = data.get("notes", "")

        existing = repo.find_by_name_and_amount(owner_id, account_id, description, amount)
        if len(existing) > 1:
            raise repo.AmbiguousMatch("Several recurring plans match; update one by id")
        if existing:
            repo.update_stream(
                owner_id,
                existing[0].id,
                cadence=frequency,
                notes=notes,
                anchor_date=anchor,
                status="confirmed",
            )
        else:
            repo.create_manual(
                owner_id,
                account_id=account_id,
                display_name=description,
                amount_cash_delta=amount,
                amount_mode=data.get("amount_mode", "fixed"),
                cadence=frequency,
                anchor_date=anchor,
                notes=notes,
            )
        return jsonify({"status": "success", "message": "Recurring transaction saved."}), 200
    except repo.RecurringError as exc:
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
        logger.error("Error saving recurring transaction: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# DELETE /accounts/<account_id>/recurringTx
# Remove a recurring transaction rule
# --------------------------------------


@recurring.route("/accounts/<account_id>/recurringTx", methods=["DELETE"])
def delete_recurring_tx(account_id):
    """End a recurring plan matched by description and amount (legacy shape).

    Several matches return 409: the caller must use the ID-based endpoint instead of guessing.
    """
    from app.services import recurring_repository as repo

    try:
        owner_id = repo.trusted_owner_id()
        data = request.get_json(silent=True) or {}
        description = data.get("description")
        amount = data.get("amount")
        if not description or amount is None:
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        matches = repo.find_by_name_and_amount(owner_id, account_id, description, amount)
        if not matches:
            return jsonify({"status": "error", "message": "No matching recurring rule found."}), 404
        if len(matches) > 1:
            raise repo.AmbiguousMatch(
                "Multiple recurring rules match this description and amount; delete by stream id instead."
            )
        repo.delete_or_end_stream(owner_id, matches[0].id)
        return jsonify({"status": "success", "message": "Recurring rule deleted."}), 200
    except repo.RecurringError as exc:
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to delete recurring transaction: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# POST /scan/<account_id>
# Auto-detect recurring transactions
# --------------------------------------


@recurring.route("/scan/<account_id>", methods=["POST"])
def scan_account_for_recurring(account_id):
    """Rescan an owned account's stored transactions for recurring candidates (idempotent).

    Uses only locally stored history (no Plaid calls): up to ``lookback_days`` (default 400, max
    1000) through ``load_v2_source_data``, which normalizes amount direction once. Candidates are
    stored as ``proposed`` streams; confirmed, ignored and ended streams keep their decision and no
    transaction is ever created. The response is the legacy reminders payload plus a ``scan`` summary
    (``history_incomplete`` is true when less history exists than was requested).
    """
    from app.services import recurring_repository as repo

    try:
        owner_id = repo.trusted_owner_id()
        repo.owned_account(owner_id, account_id)
        try:
            lookback_days = int(request.args.get("lookback_days", 400))
        except (TypeError, ValueError):
            lookback_days = 400
        lookback_days = max(30, min(lookback_days, 1000))

        from app.services.forecast_v2_sources import load_v2_source_data
        from app.services.recurring_candidate_service import detect_candidate_streams

        today = date.today()
        data = load_v2_source_data(
            user_id=owner_id,
            as_of_date=today,
            included_account_ids=[account_id],
            lookback_days=lookback_days,
        )
        found = detect_candidate_streams(data["transactions"], data["accounts"], today, lookback_days=lookback_days)
        actions = {"created": 0, "updated": 0, "preserved": 0}
        for candidate in found["candidates"]:
            _, action = repo.upsert_detected_candidate(owner_id, candidate)
            actions[action] += 1

        response, status = get_structured_recurring(account_id)
        if status != 200:
            return response, status
        payload = response.get_json()
        payload["scan"] = {
            **actions,
            "candidates": len(found["candidates"]),
            "history_days": found["history"]["days"],
            "history_incomplete": not found["history"]["complete"],
            "sign_excluded": data.get("sign_summary", {}).get("excluded", 0),
        }
        return jsonify(payload), 200
    except repo.RecurringError as exc:
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
        logger.error(
            "Error scanning account %s for recurring: %s",
            account_id,
            e,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------
# Review API: streams, candidates, scan, decisions
# --------------------------------------

PAGE_SIZE_MIN, PAGE_SIZE_MAX, PAGE_SIZE_DEFAULT = 20, 100, 50
DECISIONS = {"confirmed", "ignored", "ended"}


def _int_arg(name, default, minimum, maximum):
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _guard(handler):
    """Run ``handler(repo, owner_id)``; map repository errors to JSON and roll back on failure."""
    from app.services import recurring_repository as repo

    try:
        return handler(repo, repo.trusted_owner_id())
    except repo.RecurringError as exc:
        db.session.rollback()
        return _error_response(exc)
    except Exception as e:
        db.session.rollback()
        logger.error("Recurring review request failed: %s", e, exc_info=True)
        return jsonify({"status": "error", "message": "Unable to complete the recurring request"}), 500


@recurring.route("/streams", methods=["GET"])
def list_recurring_streams():
    """List the owner's streams: ``status`` (comma list), ``account_id``, ``page``, ``page_size`` (20-100)."""

    def run(repo, owner_id):
        statuses = [s for s in (request.args.get("status") or "").split(",") if s] or None
        if statuses and not set(statuses) <= set(repo.STATUSES):
            raise repo.ValidationFailed("status must be one of " + ", ".join(repo.STATUSES))
        streams = repo.list_streams(owner_id, account_id=request.args.get("account_id"), statuses=statuses)
        page_size = _int_arg("page_size", PAGE_SIZE_DEFAULT, PAGE_SIZE_MIN, PAGE_SIZE_MAX)
        page = _int_arg("page", 1, 1, 10_000)
        window = streams[(page - 1) * page_size : page * page_size]
        return (
            jsonify(
                {
                    "status": "success",
                    "streams": [repo.serialize_review(s) for s in window],
                    "page": page,
                    "page_size": page_size,
                    "total": len(streams),
                }
            ),
            200,
        )

    return _guard(run)


@recurring.route("/candidates", methods=["GET"])
def list_recurring_candidates():
    """Detected suggestions awaiting review (``include_ignored=true`` also returns dismissed ones)."""

    def run(repo, owner_id):
        wanted = (
            ["proposed", "ignored"] if request.args.get("include_ignored", "false").lower() == "true" else ["proposed"]
        )
        streams = [
            s
            for s in repo.list_streams(owner_id, account_id=request.args.get("account_id"), statuses=wanted)
            if s.source == "detected"
        ]
        return jsonify({"status": "success", "candidates": [repo.serialize_review(s) for s in streams]}), 200

    return _guard(run)


@recurring.route("/scan", methods=["POST"])
def scan_recurring_candidates():
    """Look for recurring patterns in stored history. Read-only unless ``dry_run`` is false.

    Body: ``account_ids`` (default: all owned accounts), ``lookback_days`` (30-1000, default 400),
    ``dry_run`` (default true). With ``dry_run: false`` all proposals are saved in one transaction;
    confirmed, ignored and ended streams are never overwritten.
    """

    def run(repo, owner_id):
        from app.services.forecast_v2_sources import load_v2_source_data
        from app.services.recurring_candidate_service import detect_candidate_streams

        data = _body()
        requested = data.get("account_ids")
        if requested is not None and not isinstance(requested, list):
            raise repo.ValidationFailed("account_ids must be a list")
        for account_id in requested or []:
            repo.owned_account(owner_id, account_id)  # 404 on any foreign id, before any work
        try:
            lookback_days = max(30, min(int(data.get("lookback_days", 400)), 1000))
        except (TypeError, ValueError):
            raise repo.ValidationFailed("lookback_days must be a number") from None
        dry_run = data.get("dry_run", True) is not False

        today = date.today()
        loaded = load_v2_source_data(
            user_id=owner_id,
            as_of_date=today,
            included_account_ids=requested or None,
            lookback_days=lookback_days,
        )
        found = detect_candidate_streams(loaded["transactions"], loaded["accounts"], today, lookback_days=lookback_days)
        summary = {"created": 0, "updated": 0, "preserved": 0}
        shown = []
        if dry_run:
            for candidate in found["candidates"]:
                shown.append(
                    {
                        "stream_id": None,
                        "candidate_key": candidate["candidate_key"],
                        "account_id": candidate["account_id"],
                        "display_name": candidate["label"],
                        "status": "candidate",
                        "cadence": candidate["cadence"],
                        "amount_mode": candidate["amount_mode"],
                        "amount_cash_delta": f"{candidate['signed_median']:.2f}",
                        "amount_range": {
                            "min": f"{candidate['amount_min']:.2f}",
                            "max": f"{candidate['amount_max']:.2f}",
                        },
                        "next_due_date": candidate["expected_next_date"].isoformat(),
                        "confidence": candidate["confidence"],
                        "evidence_count": candidate["observations"],
                        "reason_codes": candidate["reason_codes"],
                        "ready": candidate["ready"],
                    }
                )
        else:
            saved = []
            for candidate in found["candidates"]:
                stream, action = repo.upsert_detected_candidate(owner_id, candidate, commit=False)
                summary[action] += 1
                saved.append(stream)
            db.session.commit()  # one atomic write for the whole scan
            shown = [repo.serialize_review(s) for s in saved]
        return (
            jsonify(
                {
                    "status": "success",
                    "dry_run": dry_run,
                    "candidates": shown,
                    "summary": {
                        **summary,
                        "candidates": len(found["candidates"]),
                        "accounts": len(loaded["accounts"]),
                        "history_days": found["history"]["days"],
                        "history_incomplete": not found["history"]["complete"],
                        "sign_excluded": loaded.get("sign_summary", {}).get("excluded", 0),
                    },
                }
            ),
            200,
        )

    return _guard(run)


@recurring.route("/streams", methods=["POST"])
def create_recurring_stream():
    """Create a manual plan: ``account_id``, ``display_name``, ``amount_cash_delta``, ``cadence``, ``anchor_date``."""

    def run(repo, owner_id):
        data = _body()
        stream = repo.create_manual(
            owner_id,
            account_id=data.get("account_id"),
            display_name=data.get("display_name"),
            amount_cash_delta=data.get("amount_cash_delta", data.get("amount")),
            amount_mode=data.get("amount_mode", "fixed"),
            cadence=data.get("cadence"),
            anchor_date=data.get("anchor_date", data.get("next_due_date")),
            notes=data.get("notes"),
        )
        return jsonify({"status": "success", "stream": repo.serialize_review(stream)}), 201

    return _guard(run)


@recurring.route("/streams/<stream_id>", methods=["PATCH"])
def update_recurring_stream(stream_id):
    """Adjust an owned stream. Moving it to another account requires owning that account too."""

    def run(repo, owner_id):
        data = _body()
        allowed = {
            "display_name",
            "amount_cash_delta",
            "amount_mode",
            "cadence",
            "anchor_date",
            "notes",
            "account_id",
        }
        changes = {k: v for k, v in data.items() if k in allowed}
        unknown = set(data) - allowed
        if unknown:
            raise repo.ValidationFailed("cannot update: " + ", ".join(sorted(unknown)))
        stream = repo.update_stream(owner_id, stream_id, **changes)
        return jsonify({"status": "success", "stream": repo.serialize_review(stream)}), 200

    return _guard(run)


@recurring.route("/streams/<stream_id>/decision", methods=["POST"])
def decide_recurring_stream(stream_id):
    """Record the user's decision: ``confirmed``, ``ignored`` or ``ended``. Durable across rescans."""

    def run(repo, owner_id):
        decision = _body().get("decision")
        if decision not in DECISIONS:
            raise repo.ValidationFailed("decision must be one of " + ", ".join(sorted(DECISIONS)))
        stream = repo.update_stream(owner_id, stream_id, status=decision)
        return jsonify({"status": "success", "stream": repo.serialize_review(stream)}), 200

    return _guard(run)


@recurring.route("/streams/<stream_id>", methods=["DELETE"])
def delete_recurring_stream(stream_id):
    """End a stream (default, history kept) or remove it with ``?hard=true``. Transactions are untouched."""

    def run(repo, owner_id):
        hard = request.args.get("hard", "false").lower() == "true"
        action = repo.delete_or_end_stream(owner_id, stream_id, hard=hard)
        return jsonify({"status": "success", "action": action, "stream_id": stream_id}), 200

    return _guard(run)


# --------------------------------------
# GET /<account_id>/recurring
# Fetch all (user + auto) upcoming reminders
# --------------------------------------


@recurring.route("/<account_id>/recurring", methods=["GET"])
def get_structured_recurring(account_id):
    """Return a list of upcoming recurring payment reminders (user-defined + auto-detected)."""
    try:
        from app.utils.finance_utils import display_transaction_amount

        today = date.today()
        recent_cutoff = today - timedelta(days=90)
        reminders = []

        # Auto-detected reminders
        auto_rows = (
            db.session.query(
                Transaction.description,
                Transaction.amount,
                func.count(Transaction.id).label("occurrences"),
                func.max(Transaction.date).label("latest_date"),
            )
            .filter(Transaction.account_id == account_id)
            .filter(Transaction.date >= recent_cutoff)
            .group_by(Transaction.description, Transaction.amount)
            .having(func.count(Transaction.id) >= 2)
            .all()
        )

        for row in auto_rows:
            latest_date = (
                row.latest_date
                if isinstance(row.latest_date, date)
                else datetime.strptime(row.latest_date, "%Y-%m-%d").date()
            )
            next_due = add_months(latest_date, 1)
            if isinstance(next_due, datetime):
                next_due = next_due.date()
            if 0 <= (next_due - today).days <= 7:
                confidence_score = _build_auto_confidence_score(
                    occurrences=row.occurrences,
                    latest_date=latest_date,
                    recent_cutoff=recent_cutoff,
                    today=today,
                )
                dummy_tx = types.SimpleNamespace(amount=row.amount)
                reminders.append(
                    {
                        "source": "auto",
                        "account_id": account_id,
                        "description": row.description,
                        "amount": display_transaction_amount(dummy_tx),
                        "next_due_date": next_due.strftime("%Y-%m-%d"),
                        "days_until_due": (next_due - today).days,
                        "auto_detection": {
                            "occurrences": row.occurrences,
                            "latest_transaction_date": latest_date.strftime("%Y-%m-%d"),
                            "confidence_score": confidence_score,
                        },
                    }
                )

        # User-defined reminders come from confirmed recurring streams. Without a configured
        # owner no stream is read (fail closed); auto-detected reminders above are unaffected.
        streams_available = True
        try:
            from app.services import recurring_repository as repo

            owner_id = repo.trusted_owner_id()
            streams = repo.list_streams(owner_id, account_id=account_id, statuses=["confirmed"])
        except repo.RecurringError:
            streams, streams_available = [], False
        for stream in streams:
            next_due = repo.next_due_date(stream, today)
            if next_due is None or not 0 <= (next_due - today).days <= 7:
                continue
            reminders.append(
                {
                    "source": "user",
                    "account_id": account_id,
                    "stream_id": stream.id,
                    "description": stream.display_name,
                    "amount": float(stream.amount_cash_delta),
                    "next_due_date": next_due.strftime("%Y-%m-%d"),
                    "days_until_due": (next_due - today).days,
                    "notes": stream.notes,
                    "frequency": stream.cadence,
                    "auto_detection": {
                        "occurrences": 1,
                        "latest_transaction_date": next_due.strftime("%Y-%m-%d"),
                        "confidence_score": 35,
                    },
                }
            )

        return jsonify({"status": "success", "reminders": reminders, "streams_available": streams_available}), 200

    except Exception as e:
        logger.error(
            "Error fetching structured recurring transactions: %s",
            e,
            exc_info=True,
        )
        return jsonify({"status": "error", "message": str(e)}), 500
