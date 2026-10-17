"""Payday inference: synthetic dates only, no user financial data."""

import importlib
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
inference = importlib.import_module("app.services.payday_inference")
PayEvent, infer_payday = inference.PayEvent, inference.infer_payday


def events(days, amount="1500.00", payer="acme"):
    return [PayEvent(day=d, amount=Decimal(amount), payer_key=payer) for d in days]


def biweekly(start, count):
    return [start + timedelta(days=14 * i) for i in range(count)]


def test_biweekly_payroll_predicts_the_next_cycle_with_evidence():
    result = infer_payday(
        events([date(2026, 9, 4), date(2026, 9, 18), date(2026, 10, 2), date(2026, 10, 16)]), date(2026, 10, 17)
    )
    assert result["next_payday"] == "2026-10-30"
    assert result["cadence"] == "biweekly"
    assert result["source"] == "inferred_stream"
    assert result["confidence"] == "medium"
    assert result["needs_review"] is True  # inferred is never presented as confirmed
    assert result["amount_cents"] == 150000
    assert result["observed_dates"] == ["2026-09-04", "2026-09-18", "2026-10-02", "2026-10-16"]
    assert result["history_start"] == "2026-09-04" and result["history_end"] == "2026-10-16"


def test_two_cycles_are_not_enough_and_no_date_is_invented():
    result = infer_payday(events([date(2026, 10, 2), date(2026, 10, 16)]), date(2026, 10, 17))
    assert result["next_payday"] is None
    assert result["source"] == "unresolved"
    assert "insufficient_history" in result["reason_codes"]


def test_unrelated_deposits_from_different_payers_do_not_form_a_cadence():
    mixed = (
        events([date(2026, 9, 3)], payer="friend")
        + events([date(2026, 9, 20)], payer="landlord")
        + events([date(2026, 10, 9)], payer="bank refund")
    )
    result = infer_payday(mixed, date(2026, 10, 17))
    assert result["next_payday"] is None


def test_irregular_gaps_from_one_payer_are_not_a_cadence():
    result = infer_payday(
        events([date(2026, 8, 1), date(2026, 8, 9), date(2026, 9, 25), date(2026, 10, 10)]), date(2026, 10, 17)
    )
    assert result["next_payday"] is None
    assert "no_regular_payer" in result["reason_codes"]


def test_separate_payers_are_not_summed_and_the_nearest_eligible_payday_wins():
    weekly = events([date(2026, 10, 2), date(2026, 10, 9), date(2026, 10, 16)], payer="gig")
    monthly_like = events(biweekly(date(2026, 9, 4), 4), payer="acme")
    result = infer_payday(weekly + monthly_like, date(2026, 10, 17))
    assert result["next_payday"] == "2026-10-23"  # weekly gig payer, not an average of both
    assert {c["cadence"] for c in result["candidates"]} == {"weekly", "biweekly"}
    assert "multiple_payers" in result["reason_codes"]


def test_a_skipped_biweekly_cycle_still_resolves_with_a_reason():
    days = [date(2026, 8, 7), date(2026, 8, 21), date(2026, 9, 18), date(2026, 10, 2), date(2026, 10, 16)]
    result = infer_payday(events(days), date(2026, 10, 17))
    assert result["cadence"] == "biweekly"
    assert result["next_payday"] == "2026-10-30"
    assert "skipped_cycle" in result["reason_codes"]


def test_semimonthly_fifteenth_and_month_end_including_leap_february():
    days = [date(2028, 1, 31), date(2028, 2, 15), date(2028, 2, 29), date(2028, 3, 15)]
    result = infer_payday(events(days), date(2028, 3, 16))
    assert result["cadence"] == "semimonthly"
    assert result["next_payday"] == "2028-03-31"
    result = infer_payday(events(days[:3]), date(2028, 2, 29))
    assert result["next_payday"] is None  # three semimonthly dates are still ambiguous with biweekly drift


def test_monthly_on_the_31st_clamps_to_short_months():
    days = [date(2026, 7, 31), date(2026, 8, 31), date(2026, 9, 30), date(2026, 10, 31)]
    result = infer_payday(events(days), date(2026, 11, 1))
    assert result["cadence"] == "monthly"
    assert result["next_payday"] == "2026-11-30"


def test_weekly_payroll():
    result = infer_payday(events([date(2026, 10, 2), date(2026, 10, 9), date(2026, 10, 16)]), date(2026, 10, 17))
    assert (result["cadence"], result["next_payday"]) == ("weekly", "2026-10-23")


def test_two_paychecks_on_the_same_day_count_as_one_cycle():
    doubled = events([date(2026, 10, 2), date(2026, 10, 2), date(2026, 10, 16), date(2026, 10, 16)])
    result = infer_payday(doubled, date(2026, 10, 17))
    assert result["next_payday"] is None  # two distinct cycles only


def test_future_dated_deposits_are_ignored():
    result = infer_payday(events(biweekly(date(2026, 10, 16), 3)), date(2026, 10, 17))
    assert result["next_payday"] is None


def test_confirmed_stream_outranks_inference_and_is_not_flagged_for_review():
    confirmed = {"name": "Acme Payroll", "amount": Decimal("1800"), "cadence": "monthly", "next_due": date(2026, 11, 1)}
    result = infer_payday(events(biweekly(date(2026, 9, 4), 4)), date(2026, 10, 17), confirmed_streams=[confirmed])
    assert result["source"] == "confirmed_stream"
    assert result["next_payday"] == "2026-11-01"
    assert result["confidence"] == "high" and result["needs_review"] is False
    assert len(result["candidates"]) == 2


def test_user_schedule_outranks_a_confirmed_stream():
    schedule = {"name": "Me", "amount": 1000, "cadence": "weekly", "next_due": date(2026, 10, 24)}
    confirmed = {"name": "Acme", "amount": 1800, "cadence": "monthly", "next_due": date(2026, 10, 20)}
    result = infer_payday([], date(2026, 10, 17), confirmed_streams=[confirmed], user_schedule=schedule)
    assert (result["source"], result["next_payday"]) == ("user_schedule", "2026-10-24")


def test_stale_history_does_not_claim_a_payday():
    result = infer_payday(events(biweekly(date(2026, 5, 1), 4)), date(2026, 10, 17))
    assert result["next_payday"] is None


def test_stale_sync_is_flagged_but_a_valid_prediction_remains():
    result = infer_payday(events(biweekly(date(2026, 9, 4), 4)), date(2026, 10, 17), data_through=date(2026, 10, 5))
    assert result["next_payday"] == "2026-10-30"
    assert "stale_sync" in result["reason_codes"]


def test_variable_amounts_drop_the_amount_and_confidence():
    base = events(biweekly(date(2026, 9, 4), 4))
    base[1] = PayEvent(day=base[1].day, amount=Decimal("400"), payer_key="acme")
    result = infer_payday(base, date(2026, 10, 17))
    assert result["amount_cents"] is None and result["confidence"] == "low"
    assert "variable_amount" in result["reason_codes"]


def test_payer_label_is_redacted_to_one_word():
    assert inference.payer_label_for(inference.payer_key_for("ACME CORP PAYROLL PPD ID 12345 John Q Public")) == "Acme"
    assert inference.payer_key_for(None, "") == "unknown payer"
