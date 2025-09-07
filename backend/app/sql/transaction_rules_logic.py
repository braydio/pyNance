"""Helpers for persisting and applying TransactionRule models."""

from __future__ import annotations

import re
from typing import Any, Dict

from app.extensions import db
from app.models import Category, TransactionRule


def create_rule(
    user_id: str, match_criteria: Dict[str, Any], action: Dict[str, Any]
) -> TransactionRule:
    """Insert a TransactionRule row and return it."""
    rule = TransactionRule(
        user_id=user_id, match_criteria=match_criteria, action=action
    )
    db.session.add(rule)
    db.session.commit()
    return rule


def get_applicable_rules(user_id: str) -> list[TransactionRule]:
    """Return active rules for a user ordered by creation."""
    return (
        TransactionRule.query.filter_by(user_id=user_id, is_active=True)
        .order_by(TransactionRule.created_at.asc())
        .all()
    )


def apply_rules(user_id: str, transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate a transaction dict based on matching rules."""
    rules = get_applicable_rules(user_id)
    for rule in rules:
        crit = rule.match_criteria or {}
        match = True
        if "merchant_name" in crit and crit["merchant_name"] != transaction.get(
            "merchant_name"
        ):
            match = False
        pattern = crit.get("description_pattern")
        if (
            match
            and pattern
            and not re.search(
                pattern, transaction.get("description", ""), re.IGNORECASE
            )
        ):
            match = False
        if (
            match
            and "amount_min" in crit
            and transaction.get("amount", 0) < crit["amount_min"]
        ):
            match = False
        if (
            match
            and "amount_max" in crit
            and transaction.get("amount", 0) > crit["amount_max"]
        ):
            match = False
        if not match:
            continue
        for key, value in (rule.action or {}).items():
            if key == "category_id":
                category = Category.query.get(value)
                if category:
                    transaction["category_id"] = category.id
                    transaction["category"] = category.display_name
            else:
                transaction[key] = value
        transaction["updated_by_rule"] = True
        break
    return transaction
