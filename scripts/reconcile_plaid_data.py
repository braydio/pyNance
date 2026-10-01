#!/usr/bin/env python3
"""Reconcile retained Plaid evidence; dry run by default, never call Plaid."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Commit the reconciled data after validation")
    parser.add_argument("--migrate", action="store_true", help="Apply the audit migration before reconciliation")
    parser.add_argument("--report", type=Path, required=True, help="Private JSON change report outside the repository")
    args = parser.parse_args()
    from dotenv import dotenv_values
    from flask import Flask
    from sqlalchemy import text

    config = dotenv_values(ROOT / "backend/.env")
    uri = os.environ.get("PYNANCE_RECONCILE_DATABASE_URI") or config["SQLALCHEMY_DATABASE_URI"]
    schema = config.get("DB_SCHEMA", "public")
    # Import application modules with the selected configuration, without
    # launching the app factory, jobs, routes, or any provider calls.
    os.environ["SQLALCHEMY_DATABASE_URI"] = uri
    os.environ["DB_SCHEMA"] = schema
    from app.extensions import db
    from app.models import Account, PlaidSourceEvent, Transaction, TransactionRule
    from app.services.plaid_audit import (
        clear_transfer,
        ingestion_lock,
        modified_fields,
        record_source,
        retire_transaction,
        source_context,
    )
    from app.services.plaid_sync import _parse_txn_date
    from app.sql.account_logic import detect_internal_transfer, get_or_create_category
    from app.sql.transaction_rules_logic import resolve_category_label
    from app.utils.merchant_normalization import resolve_merchant

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=uri,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"options": f"-c search_path={schema}"}},
    )
    db.init_app(app)
    run_id = str(uuid4())
    changes = []
    unresolved = []
    counts = Counter()
    with app.app_context():
        if args.migrate:
            if not args.apply:
                raise SystemExit("Migration requires --apply; rehearse against an isolated restore first")
            from alembic.migration import MigrationContext
            from alembic.operations import Operations

            with db.engine.begin() as connection:
                revision = connection.execute(text("select version_num from alembic_version")).scalar_one()
                if revision == "a3c8e1f4b2d7":
                    path = ROOT / "backend/migrations/versions/e6a9c2f4b8d1_plaid_source_audit_and_category_identity.py"
                    spec = importlib.util.spec_from_file_location("audit_migration", path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    with Operations.context(MigrationContext.configure(connection)):
                        module.upgrade()
                    connection.execute(text("update alembic_version set version_num='e6a9c2f4b8d1'"))
                elif revision != "e6a9c2f4b8d1":
                    raise RuntimeError("Unexpected migration revision; use the repository migration workflow")
        try:
            db.session.execute(text("SET LOCAL lock_timeout='15s'"))
            for owner in sorted({a.user_id for a in Account.query.all() if a.user_id}):
                ingestion_lock("plaid-owner:" + owner)
            ingestion_lock("plaid-categories")
            # Coordinate with writers, then freeze the evidence for this repair.
            # Legacy writers also touch these tables; a lock timeout rolls back.
            db.session.execute(
                text(
                    "LOCK TABLE accounts, plaid_accounts, transactions, plaid_transaction_meta, categories, transaction_rules, transaction_tags, recurring_transactions IN SHARE ROW EXCLUSIVE MODE"
                )
            )
            transactions = Transaction.query.order_by(Transaction.id).all()
            accounts = {a.account_id: a for a in Account.query.all()}
            before_count = len(transactions)
            old = {
                t.transaction_id: {column.name: getattr(t, column.name) for column in Transaction.__table__.columns}
                for t in transactions
            }
            with source_context(run_id=run_id, endpoint="local/reconciliation"):
                for t in transactions:
                    raw = deepcopy(t.plaid_meta.raw) if t.plaid_meta else None
                    # This is a baseline of retained evidence, not a claim to
                    # recover provider originals that have already been lost.
                    record_source(
                        {
                            "transaction_id": t.transaction_id,
                            "account_id": t.account_id,
                            "source": raw,
                            "local": old[t.transaction_id],
                        },
                        event_type="baseline",
                    )
                    a = accounts.get(t.account_id)
                    if not a or not a.user_id or (t.user_id and t.user_id != a.user_id):
                        raise ValueError("Transaction/account ownership requires manual resolution")
                    if t.user_id != a.user_id:
                        t.user_id = a.user_id
                        counts["owners_fixed"] += 1
                    if not raw:
                        unresolved.append({"id": t.id, "reason": "missing_source"})
                        continue
                    protected = modified_fields(t)
                    if "date" not in protected and raw.get("date"):
                        source_date = _parse_txn_date(raw["date"])
                        if t.date != source_date:
                            t.date = source_date
                            counts["dates_fixed"] += 1
                    if protected & {"category", "category_id", "category_slug", "category_display"}:
                        # Retain explicit user labels; repair their stale linked
                        # identity instead of assigning a different PFC meaning.
                        if t.category and len(t.category.strip()) > 1:
                            category = resolve_category_label(t.category)
                        else:
                            # A one-character test label is not a meaningful
                            # classification; restore the retained provider PFC.
                            pfc = raw.get("personal_finance_category") or {}
                            path = raw.get("category") or []
                            category = get_or_create_category(
                                path[0] if path else "Unknown",
                                path[1] if len(path) > 1 else "Unknown",
                                pfc.get("primary"),
                                pfc.get("detailed"),
                                raw.get("personal_finance_category_icon_url"),
                            )
                            fields = {
                                key: True
                                for key in protected
                                if key not in {"category", "category_id", "category_slug", "category_display"}
                            }
                            t.user_modified_fields = json.dumps(fields)
                            t.user_modified = bool(fields)
                            counts["invalid_user_categories_fixed"] += 1
                    else:
                        pfc = raw.get("personal_finance_category") or {}
                        path = raw.get("category") or []
                        if not isinstance(path, (list, tuple)):
                            path = []
                        category = get_or_create_category(
                            path[0] if path else "Unknown",
                            path[1] if len(path) > 1 else "Unknown",
                            pfc.get("primary"),
                            pfc.get("detailed"),
                            raw.get("personal_finance_category_icon_url"),
                        )
                    desired = dict(
                        category_id=category.id,
                        category=category.computed_display_name,
                        category_slug=category.category_slug,
                        category_display=category.computed_display_name,
                    )
                    if any(getattr(t, k) != v for k, v in desired.items()):
                        for k, v in desired.items():
                            setattr(t, k, v)
                        counts["categories_fixed"] += 1
                    if "merchant_name" not in protected and (
                        not t.merchant_name or t.merchant_name.lower() == "unknown"
                    ):
                        merchant = resolve_merchant(
                            raw.get("merchant_name") if raw.get("merchant_name") != "Unknown" else None,
                            raw.get("name"),
                            raw.get("description"),
                        )
                        if merchant.display_name != "Unknown":
                            t.merchant_name = merchant.display_name
                            t.merchant_slug = merchant.merchant_slug
                            counts["merchants_fixed"] += 1
                db.session.flush()
                # Only retire explicit provider-linked pending predecessors.
                for posted in list(transactions):
                    if posted.pending or not posted.plaid_meta:
                        continue
                    predecessor_id = posted.plaid_meta.pending_transaction_id
                    if not predecessor_id:
                        continue
                    predecessor = Transaction.query.filter_by(transaction_id=predecessor_id).first()
                    if predecessor:
                        if not predecessor.pending or predecessor.account_id != posted.account_id:
                            raise ValueError("Invalid pending predecessor link")
                        retire_transaction(predecessor, reason="pending_replaced", successor=posted)
                        counts["pending_retired"] += 1
                remaining = Transaction.query.order_by(Transaction.date, Transaction.transaction_id).all()
                # Clear only automatic links, retaining the user's explicit
                # decisions. Rebuild after dates/categories/pending are repaired.
                for t in remaining:
                    if "is_internal" not in modified_fields(t) and (t.is_internal or t.internal_match_id):
                        clear_transfer(t)
                db.session.flush()
                for t in remaining:
                    detect_internal_transfer(t)
                db.session.flush()
                for t in remaining:
                    after = {column.name: getattr(t, column.name) for column in Transaction.__table__.columns}
                    delta = {
                        k: {"before": old[t.transaction_id][k], "after": v}
                        for k, v in after.items()
                        if old[t.transaction_id][k] != v
                    }
                    if not old[t.transaction_id]["is_internal"] and t.is_internal:
                        counts["transfer_rows_newly_flagged"] += 1
                    elif old[t.transaction_id]["is_internal"] and not t.is_internal:
                        counts["transfer_rows_unflagged"] += 1
                    if old[t.transaction_id]["internal_match_id"] != t.internal_match_id:
                        counts["transfer_links_repaired"] += 1
                    if delta:
                        changes.append({"id": t.id, "transaction_id": t.transaction_id, "fields": delta})
                        record_source(
                            {"transaction_id": t.transaction_id, "account_id": t.account_id, "changes": delta},
                            event_type="corrected",
                        )
                    if t.internal_match_id:
                        other = Transaction.query.filter_by(transaction_id=t.internal_match_id).first()
                        if (
                            not other
                            or other.internal_match_id != t.transaction_id
                            or not other.is_internal
                            or t.pending
                            or other.pending
                        ):
                            raise ValueError("Invalid transfer links remain after reconciliation")
                # Fix the accidental one-character merchant rule which would
                # otherwise corrupt the next provider refresh again.
                for rule in TransactionRule.query.all():
                    action = dict(rule.action or {})
                    if (
                        action.get("merchant_name") == "r"
                        and (rule.match_criteria or {}).get("description_pattern") == "^Tony's\\ Tobacco\\ \\&\\ Vapor$"
                    ):
                        original = deepcopy(action)
                        action["merchant_name"] = "Tony's Tobacco & Vapor"
                        rule.action = action
                        record_source(
                            {
                                "transaction_id": "rule:" + str(rule.id),
                                "rule_id": rule.id,
                                "before": original,
                                "after": action,
                            },
                            event_type="rule_corrected",
                        )
                        counts["rules_fixed"] += 1
                validations = {
                    "ownership_mismatches": db.session.execute(
                        text(
                            "select count(*) from transactions t join accounts a using(account_id) where t.user_id is distinct from a.user_id"
                        )
                    ).scalar(),
                    "pending_posted_coexistence": db.session.execute(
                        text(
                            "select count(*) from transactions t join plaid_transaction_meta m using(transaction_id) join transactions p on p.transaction_id=m.pending_transaction_id where not t.pending and p.pending"
                        )
                    ).scalar(),
                    "duplicate_ids": db.session.execute(
                        text(
                            "select count(*) from (select transaction_id from transactions group by transaction_id having count(*)>1) d"
                        )
                    ).scalar(),
                }
                if any(validations.values()):
                    raise ValueError("Reconciliation invariants failed")
                result = {
                    "run_id": run_id,
                    "applied": False,
                    "requested_apply": args.apply,
                    "status": "prepared",
                    "schema": schema,
                    "before_count": before_count,
                    "after_count": len(remaining),
                    "counts": dict(counts),
                    "changes": changes,
                    "unresolved": unresolved,
                    "validations": validations,
                    "internal_count": sum(bool(t.is_internal) for t in remaining),
                    "audit_events": PlaidSourceEvent.query.filter_by(run_id=run_id).count(),
                }
                # Materialize the report before committing; failure to write it
                # aborts rather than applying undocumented changes.
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps(result, default=str, indent=2))
                os.chmod(args.report, 0o600)
                if args.apply:
                    db.session.commit()
                else:
                    db.session.rollback()
                result["applied"] = args.apply
                result["status"] = "committed" if args.apply else "rehearsed_and_rolled_back"
                args.report.write_text(json.dumps(result, default=str, indent=2))
            print(json.dumps({k: v for k, v in result.items() if k not in {"changes", "unresolved"}}, indent=2))
            print("Unresolved records:", len(unresolved))
        except Exception:
            db.session.rollback()
            raise


if __name__ == "__main__":
    main()
