"""Pure tests for recurring cash obligation projection (synthetic data, no database or network)."""

import importlib.util
import os
import sys
from datetime import date

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, BACKEND)
spec = importlib.util.spec_from_file_location(
    "recurring_obligation_projection_under_test",
    os.path.join(BACKEND, "app", "services", "recurring_obligation_projection.py"),
)
proj = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = proj
spec.loader.exec_module(proj)

AS_OF = date(2026, 10, 17)
END = date(2026, 10, 30)  # day before a payday on Oct 31


def stream(stream_id="s1", **overrides):
    values = dict(
        stream_id=stream_id,
        account_id="chk",
        name="Rent",
        merchant_key="rent",
        amount_cents=70_000,
        amount_mode="fixed",
        cadence="monthly",
        anchor_date=date(2026, 7, 21),
        status="confirmed",
        source="manual",
        confidence=None,
        evidence_cycles=3,
        last_observed=date(2026, 9, 21),
    )
    values.update(overrides)
    return proj.StreamInput(**values)


def candidate(**overrides):
    return stream(**{"status": "proposed", "source": "detected", "confidence": 0.9, **overrides})


def run(streams=(), bills=(), posted=(), as_of=AS_OF, end=END, display_end=None):
    return proj.project_cash_obligations(streams, bills, posted, as_of, end, display_end or as_of)


def test_confirmed_monthly_debit_is_reserved_once_but_not_due_today():
    result = run([stream()])
    assert [(r["due_date"], r["amount_cents"], r["status"]) for r in result["rows"]] == [
        ("2026-10-21", 70_000, "confirmed")
    ]
    assert result["totals"]["confirmed"] == result["totals"]["protection_reserved"] == 70_000
    assert result["totals"]["display_due"] == 0  # reserved by the protection horizon, not due today
    assert result["rows"][0]["in_display_window"] is False


def test_provisional_requires_three_cycles_and_confidence_and_fresh_evidence():
    ok = run([candidate()])
    assert ok["rows"][0]["status"] == "provisional" and ok["totals"]["provisional"] == 70_000
    two = run([candidate(evidence_cycles=2)])
    assert two["rows"] == [] and two["totals"]["needs_review"] == 70_000
    assert two["needs_review"][0]["reason_codes"][0] == "needs_review_insufficient_cycles"
    low = run([candidate(confidence=0.8)])
    assert low["rows"] == [] and low["needs_review"][0]["reason_codes"][0] == "needs_review_low_confidence"
    stale = run([candidate(last_observed=date(2026, 5, 21))])
    assert stale["rows"] == [] and stale["needs_review"][0]["reason_codes"][0] == "stale_evidence"


def test_ignored_ended_and_ineligible_streams_never_reserve():
    result = run(
        [
            stream("a", status="ignored"),
            stream("b", status="ended"),
            stream("c", eligible=False, ineligible_reason="own_account_transfer"),
            stream("d", eligible=False, ineligible_reason="card_purchase"),
            stream("e", amount_cents=0),
        ]
    )
    assert result["rows"] == [] and result["totals"]["protection_reserved"] == 0
    assert {s["reason"] for s in result["skipped"]} >= {"own_account_transfer", "card_purchase", "ambiguous_sign"}


def test_planned_bill_supersedes_matching_stream_and_distinct_plan_stays():
    bill = proj.PlannedBillInput("b1", "Rent", "chk", date(2026, 10, 21), 70_000)
    other = proj.PlannedBillInput("b2", "Rent", "chk", date(2026, 10, 22), 12_000)
    result = run([stream()], [bill, other])
    assert result["totals"]["protection_reserved"] == 82_000  # $700 once + the separate $120 plan
    assert {r["source"] for r in result["rows"]} == {"planned_bill"}
    # A near-date match with a different amount is a different bill, not a duplicate.
    different = run([stream()], [proj.PlannedBillInput("b3", "Rent", "chk", date(2026, 10, 20), 65_000)])
    assert different["totals"]["protection_reserved"] == 135_000


def test_ambiguous_planned_match_keeps_the_recurring_row():
    a = proj.PlannedBillInput("b1", "Rent", "chk", date(2026, 10, 20), 70_000)
    b = proj.PlannedBillInput("b2", "Rent", "chk", date(2026, 10, 22), 70_000)
    assert run([stream()], [a, b])["totals"]["protection_reserved"] == 210_000


def test_month_end_anchor_clamps_to_february():
    result = run([stream(anchor_date=date(2026, 1, 31))], as_of=date(2027, 2, 20), end=date(2027, 3, 5))
    assert [r["due_date"] for r in result["rows"]] == ["2027-02-28"]


def test_variable_amount_uses_conservative_upper_quartile_not_certainty():
    variable = candidate(
        amount_mode="variable", amount_cents=70_000, evidence_amounts_cents=(67_000, 70_000, 73_000, 150_000)
    )
    row = run([variable])["rows"][0]
    assert row["estimated"] is True and "estimated_amount" in row["reason_codes"]
    assert row["amount_cents"] == 73_000 and row["amount_range_cents"] == {"min": 67_000, "max": 73_000}
    manual = run([stream(amount_mode="variable")])["rows"][0]
    assert manual["amount_cents"] == 70_000 and manual["estimated"] is False


def test_posted_payment_is_not_reserved_again():
    paid = proj.PostedOutflow("chk", date(2026, 10, 16), 70_000)
    result = run([stream(anchor_date=date(2026, 7, 17))], posted=[paid])
    assert result["rows"] == [] and result["skipped"][0]["reason"] == "already_paid"
    other_account = proj.PostedOutflow("sav", date(2026, 10, 16), 70_000)
    assert len(run([stream(anchor_date=date(2026, 7, 17))], posted=[other_account])["rows"]) == 1


def test_biweekly_and_semimonthly_expand_every_occurrence():
    biweekly = run([stream(cadence="biweekly", amount_cents=1_000, anchor_date=date(2026, 10, 2))])
    assert [r["due_date"] for r in biweekly["rows"]] == ["2026-10-30"]
    semi = run([stream(cadence="semimonthly", amount_cents=500, anchor_date=date(2026, 9, 1))])
    assert [r["due_date"] for r in semi["rows"]] == []  # Oct 1 and Oct 16 are before as_of
    semi = run([stream(cadence="semimonthly", amount_cents=500, anchor_date=date(2026, 9, 5))], end=date(2026, 11, 2))
    assert [r["due_date"] for r in semi["rows"]] == ["2026-10-20"]


def test_history_coverage_codes():
    assert proj.history_coverage(None, AS_OF) == ["no_transactions"]
    assert proj.history_coverage(date(2026, 9, 1), AS_OF) == ["partial_history"]
    assert proj.history_coverage(date(2026, 1, 1), AS_OF) == []
