"""app.models package exports.

This package exposes all SQLAlchemy models grouped into modules.
"""

from .account_models import (
    Account,
    AccountGroup,
    AccountGroupMembership,
    AccountGroupPreference,
    AccountHistory,
    AccountSnapshotPreference,
    FinancialGoal,
)

# Application settings
from .app_settings import LlmSettings

# Institutions & linked accounts
from .institution_models import Institution, PlaidAccount, PlaidItem, PlaidWebhookLog
from .investment_models import InvestmentHolding, InvestmentTransaction, Security

# Mixins
from .mixins import TimestampMixin

# Planning
from .planning_models import AllocationType, PlannedBill, PlanningScenario, ScenarioAllocation

# Transactions
from .transaction_models import (
    Category,
    PlaidSourceEvent,
    PlaidTransactionMeta,
    RecurringTransaction,
    Tag,
    Transaction,
    TransactionRule,
    transaction_tags,
)

__all__ = [
    # Mixins
    "TimestampMixin",
    "LlmSettings",
    # Institutions
    "Institution",
    "PlaidAccount",
    "PlaidItem",
    "PlaidWebhookLog",
    # Accounts
    "Account",
    "AccountGroup",
    "AccountGroupMembership",
    "AccountGroupPreference",
    "AccountHistory",
    "AccountSnapshotPreference",
    "FinancialGoal",
    # Transactions
    "Category",
    "Tag",
    "Transaction",
    "transaction_tags",
    "RecurringTransaction",
    "TransactionRule",
    "PlaidTransactionMeta",
    "PlaidSourceEvent",
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
