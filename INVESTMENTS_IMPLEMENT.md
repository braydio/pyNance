Awesome next-level ask—I’d be glad to draft a complete development roadmap for the Investments feature in your pyNance project, aligned with how your Transactions module is built. Here’s a roadmap outline that includes file structure, backend API, SQL schema, upsert logic, Plaid integration, and visualization—each matched to analogous Transaction components.

⸻

1. Overview of Plaid Investments Endpoints

Plaid provides investment-related endpoints:
• Holdings: /investments/holdings/get → returns both securities (metadata like ticker, name, price) and holdings (user-specific: quantity, cost basis, value) ￼ ￼.
• Transactions: /investments/transactions/get → returns investment-account specific transactions (e.g., dividends, buys, sells), with fields like security_id, amount, quantity, price, subtype, etc. ￼.
• Python client is fully supported via plaid-python: use client.Holdings.get(...) and client.InvestmentTransactions.get(...) with appropriate parameters ￼.

⸻

2. High-Level Roadmap File Structure & Matching

Here’s a proposed directory and file structure, matched to existing Transactions files:

backend/app/services/investments_service.py # matches transactions_service.py
backend/app/api/investments.py # matches transactions routes handler
backend/app/schemas/investments_schemas.py # matches transactions schemas
docs/backend/features/investments.md # matches docs/backend/features/transactions.md
docs/backend/load_investments.md # matches docs/backend/load_transactions.md
docs/backend/cron_investments_sync.md # matches cron_sync for transactions

⸻

3. SQL Schema: New Tables

Analogous to transactions, propose:

-- securities: metadata about investment instruments
CREATE TABLE securities (
security_id TEXT PRIMARY KEY,
name TEXT,
ticker_symbol TEXT,
cusip TEXT,
isin TEXT,
type TEXT,
is_cash_equivalent BOOLEAN,
institution_price NUMERIC,
institution_price_as_of DATE,
market_identifier_code TEXT,
iso_currency_code TEXT
);

-- holdings: user-specific positions
CREATE TABLE holdings (
holding_id SERIAL PRIMARY KEY,
account_id TEXT,
security_id TEXT REFERENCES securities(security_id),
quantity NUMERIC,
cost_basis NUMERIC,
institution_value NUMERIC,
as_of DATE,
UNIQUE(account_id, security_id)
);

-- investment_transactions: investment-specific transactions
CREATE TABLE investment_transactions (
investment_transaction_id TEXT PRIMARY KEY,
account_id TEXT,
security_id TEXT REFERENCES securities(security_id),
date DATE,
amount NUMERIC,
price NUMERIC,
quantity NUMERIC,
subtype TEXT,
type TEXT,
name TEXT,
fees NUMERIC,
iso_currency_code TEXT
);

⸻

4. Backend Service: investments_service.py

# backend/app/services/investments_service.py

from plaid.api import plaid_api
from plaid.model import InvestmentsHoldingsGetRequest, InvestmentsTransactionsGetRequest

from .db import db_session
from .models import Security, Holding, InvestmentTransaction

class InvestmentsService:
def **init**(self, client: plaid_api.PlaidApi):
self.client = client

    def fetch_and_upsert_holdings(self, access_token):
        req = InvestmentsHoldingsGetRequest(access_token=access_token)
        resp = self.client.investments_holdings_get(req)
        data = resp.to_dict()

        # Upsert securities
        for sec in data["securities"]:
            db_session.merge(Security(**sec))
        # Upsert holdings
        for h in data["holdings"]:
            holding = Holding(
                account_id=h["account_id"],
                security_id=h["security_id"],
                quantity=h["quantity"],
                cost_basis=h.get("cost_basis"),
                institution_value=h.get("institution_value"),
                as_of=h.get("institution_price_as_of")
            )
            db_session.merge(holding)
        db_session.commit()

    def fetch_and_upsert_transactions(self, access_token, start_date, end_date):
        req = InvestmentsTransactionsGetRequest(
            access_token=access_token, start_date=start_date, end_date=end_date
        )
        resp = self.client.investments_transactions_get(req)
        data = resp.to_dict()

        for tx in data["investment_transactions"]:
            inv_tx = InvestmentTransaction(**tx)
            db_session.merge(inv_tx)
        db_session.commit()

This parallels your transactions service logic but uses the investments-specific endpoints.

⸻

5. API Routing: api/investments.py

# backend/app/api/investments.py

from fastapi import APIRouter, Depends
from typing import List
from datetime import date

from ..services.investments_service import InvestmentsService
from ..schemas.investments_schemas import HoldingSchema, InvestmentTransactionSchema
from ..dependencies import get_plaid_client, get_db

router = APIRouter(prefix="/investments", tags=["Investments"])

@router.post("/sync", response_model=dict)
def sync_investments(
access_token: str,
start_date: date,
end_date: date,
svc: InvestmentsService = Depends(),
):
svc.fetch_and_upsert_holdings(access_token)
svc.fetch_and_upsert_transactions(access_token, start_date, end_date)
return {"status": "ok"}

@router.get("/holdings", response_model=List[HoldingSchema])
def list_holdings(db=Depends(get_db)):
return db.query(Holding).all()

@router.get("/transactions", response_model=List[InvestmentTransactionSchema])
def list_transactions(db=Depends(get_db)):
return db.query(InvestmentTransaction).all()

This matches your existing transactions routing structure but uses UBS-specific models.

⸻

6. Schemas: schemas/investments_schemas.py

# backend/app/schemas/investments_schemas.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

class HoldingSchema(BaseModel):
account_id: str
security_id: str
quantity: float
cost_basis: Optional[float]
institution_value: Optional[float]
as_of: Optional[date]

class InvestmentTransactionSchema(BaseModel):
investment_transaction_id: str
account_id: str
security_id: str
date: date
amount: float
price: float
quantity: float
subtype: Optional[str]
type: Optional[str]
name: Optional[str]
fees: Optional[float]
iso_currency_code: Optional[str]

Modeled after transaction schemas.

⸻

7. Documentation Files

docs/backend/features/investments.md

Cover:
• Purpose & use-cases
• API endpoints (/investments/sync, holdings, transactions)
• Data flow: Link → sync → holdings + transactions

docs/backend/load_investments.md

Document step-by-step how to run the sync service, including required parameters and environment.

docs/backend/cron_investments_sync.md

Explain how to schedule daily or on-demand sync, analogous to your cron docs for transactions.

⸻

8. Visuals & Diagrams (Docs)

In docs/backend/features/investments.md, include:
• Sequence diagram: 1. User triggers sync (via UI or cron). 2. Server calls Plaid Holdings endpoint. 3. Holds upsert into securities + holdings. 4. Server calls Plaid Transactions endpoint. 5. Upserts investment_transactions. 6. UI queries holdings/transactions endpoints to present data.
• ER diagram of new tables: securities ⇄ holdings and separately investment_transactions.

⸻

9. Summary Table: Matching with Transactions Module

Component Transactions Counterpart Investments Counterpart
Service transactions_service.py investments_service.py
API Routing api/transactions.py api/investments.py
Schemas schemas/transactions_schemas.py schemas/investments_schemas.py
SQL Tables transactions, etc. securities, holdings, investment_transactions
Load Docs load_transactions.md load_investments.md
Cron Sync Docs cron_sync.md cron_investments_sync.md
Feature Doc features/transactions.md features/investments.md

⸻

Next Steps for Execution

Once you hand this plan to ChatGPT (or me again): 1. Create the blank files using GitHub SDK (e.g., service, routing, schemas, docs). 2. Write the SQL migrations to create tables. 3. Implement service logic, inject dependencies (plaid_client, db_session). 4. Add API endpoints, test via API clients. 5. Update documentation with visuals and usage instructions. 6. Schedule sync tasks (cron or job runner). 7. Add UI components or frontend integrations (if needed).

⸻

Let me know if you’d like me to draft the actual file contents and push them to the repo, or generate the diagram visuals as ASCII or Markdown.
