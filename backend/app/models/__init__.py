"""app.models package exports.

This package exposes all SQLAlchemy models grouped into modules.
"""

# Accounts
from .account_models import (
    Account,
    AccountHistory,
    AccountSnapshotPreference,
    FinancialGoal,
)

# Institutions & linked accounts
from .institution_models import (
    Institution,
    PlaidAccount,
    PlaidItem,
    PlaidWebhookLog,
    TellerAccount,
)
from .investment_models import (
    InvestmentHolding,
    InvestmentTransaction,
    Security,
)

# Mixins
from .mixins import TimestampMixin

# Planning
from .planning_models import (
    AllocationType,
    PlannedBill,
    PlanningScenario,
    ScenarioAllocation,
)

# Transactions
from .transaction_models import (
    Category,
    PlaidTransactionMeta,
    RecurringTransaction,
    Transaction,
    TransactionRule,
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
    "AccountSnapshotPreference",
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
    # Investments
    "Security",
    "InvestmentHolding",
    "InvestmentTransaction",
]
