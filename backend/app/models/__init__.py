"""app.models package exports.

This package exposes all SQLAlchemy models grouped into modules.
"""

# Mixins
from .mixins import TimestampMixin

# Institutions & linked accounts
from .institution_models import (
    Institution,
    PlaidAccount,
    PlaidItem,
    PlaidWebhookLog,
    TellerAccount,
)

# Accounts
from .account_models import Account, AccountHistory, FinancialGoal

# Transactions
from .transaction_models import (
    Category,
    Transaction,
    RecurringTransaction,
    TransactionRule,
    PlaidTransactionMeta,
)

# Planning
from .planning_models import (
    AllocationType,
    PlanningScenario,
    PlannedBill,
    ScenarioAllocation,
)


__all__ = [
    # Mixins
    "TimestampMixin",
    # Institutions
    "Institution",
    "PlaidAccount",
    "PlaidItem",
    "PlaidWebhookLog",
    "TellerAccount",
    # Accounts
    "Account",
    "AccountHistory",
    "FinancialGoal",
    # Transactions
    "Category",
    "Transaction",
    "RecurringTransaction",
    "TransactionRule",
    "PlaidTransactionMeta",
    # Planning
    "AllocationType",
    "PlanningScenario",
    "PlannedBill",
    "ScenarioAllocation",
]
