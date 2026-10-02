# Task Packet: Safe-to-Spend Reliability + Correct Cashflow Semantics

**Date:** 2026-10-02  
**Status:** Ready to implement  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Workstream size:** One compact implementation packet  
**Goal:** Fix the dashboard Safe-to-Spend card so it reliably loads, exposes useful backend failures, applies the correct Plaid cashflow sign convention, and does not lose transactions because of null Transaction.user_id values.

---

## 1. Do not rediscover the feature

The relevant implementation is already known.

Primary files:

- frontend/src/views/Dashboard.vue
- frontend/src/services/api.js
- backend/app/routes/dashboard.py
- backend/app/services/safe_to_spend.py
- backend/app/sql/account_logic.py
- backend/app/services/plaid_sync.py
- backend/migrations/versions/6b0f2c9d1a34_add_planning_persistence_tables.py
- render.yaml
- tests/test_safe_to_spend_service.py
- tests/test_dashboard_activity_status_route.py
- frontend/src/components/dashboard/__tests__/SafeToSpendCard.spec.ts

Do not perform a repo-wide architecture pass before implementing this packet.

---

## 2. Current failure

Dashboard.vue currently collapses every thrown Safe-to-Spend request error to:

    Unable to calculate spend room.

Relevant code is around frontend/src/views/Dashboard.vue:487-506.

The backend route is:

    GET /api/dashboard/safe-to-spend

in backend/app/routes/dashboard.py:32-58.

The service always executes:

    _visible_accounts()
    _next_income_date()
    _upcoming_bill_payload()
    _spent_between()

The planning query in _upcoming_bill_payload() requires:

- planning_scenarios
- planned_bills

Those tables are created by the existing migration:

    backend/migrations/versions/6b0f2c9d1a34_add_planning_persistence_tables.py

Docker runs migrations automatically in backend/docker-entrypoint.sh.

render.yaml currently starts Gunicorn directly and does not apply migrations.

Do not create another planning-table migration. Ensure the existing migration chain is applied.

---

# 3. Required corrections

## 3.1 Surface the actual API error in Dashboard.vue

File:

    frontend/src/views/Dashboard.vue

Current catch:

    } catch (error) {
      if (token !== safeToSpendToken) return
      console.error('Failed to load safe-to-spend guidance:', error)
      safeToSpendError.value = 'Unable to calculate spend room.'
    }

Replace with an extracted server message while retaining the fallback:

    } catch (error) {
      if (token !== safeToSpendToken) return

      console.error('Failed to load safe-to-spend guidance:', error)

      safeToSpendError.value =
        error?.response?.data?.message ||
        error?.message ||
        'Unable to calculate spend room.'
    }

Do not alter SafeToSpendCard.vue merely to solve this error-reporting issue. It already renders the passed error string.

Add/update a Dashboard unit test proving a backend 500 message reaches safeToSpendError.

Do not expose stack traces or raw HTML responses.

---

## 3.2 Make Safe-to-Spend transaction signs provider-aware

File:

    backend/app/services/safe_to_spend.py

Important storage fact:

backend/app/services/plaid_sync.py writes Plaid amounts directly:

    amount=tx.get("amount")

Plaid raw transaction semantics are:

- positive amount = money leaving the account
- negative amount = money entering the account

The current Safe-to-Spend code does the opposite:

    Transaction.amount < 0   # current spend filter
    Transaction.amount > 0   # current income candidate filter

Do NOT globally invert every transaction because non-Plaid/manual data has historically used the existing sign convention.

Implement explicit provider-aware predicates.

Add sqlalchemy.and_ to the imports:

    from sqlalchemy import and_, func, or_

Recommended helper predicates:

    def _outflow_filter():
        return or_(
            and_(Transaction.provider == "plaid", Transaction.amount > 0),
            and_(Transaction.provider != "plaid", Transaction.amount < 0),
        )


    def _inflow_filter():
        return or_(
            and_(Transaction.provider == "plaid", Transaction.amount < 0),
            and_(Transaction.provider != "plaid", Transaction.amount > 0),
        )

If SQLAlchemy enum comparison requires a different local form, use the equivalent expression while preserving these semantics.

Then change _spent_between():

Current:

    .filter(Transaction.amount < 0)

Target:

    .filter(_outflow_filter())

Keep:

    func.sum(func.abs(Transaction.amount))

so the result remains a positive spend amount.

Change _next_income_date():

Current:

    .filter(Transaction.amount > 0)

Target:

    .filter(_inflow_filter())

Keep _looks_like_income() as the second-stage metadata/category check.

Do not change the stored Plaid transaction sign convention in this packet.

---

## 3.3 Scope Safe-to-Spend through Account.user_id, not Transaction.user_id

File:

    backend/app/services/safe_to_spend.py

Both relevant queries already join Account:

    .join(Account, Account.account_id == Transaction.account_id)

Current scoped filters use:

    Transaction.user_id == user_id

Replace those with:

    Account.user_id == user_id

Specifically update:

- _spent_between()
- _next_income_date()

Reason:

- Account is the canonical owner of the transaction.
- older/alternate ingestion paths can contain null Transaction.user_id.
- Safe-to-Spend should not silently exclude a transaction that belongs to a correctly scoped Account.

Recommended resulting pattern in _spent_between():

    query = (
        db.session.query(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .join(Account, Account.account_id == Transaction.account_id)
        .filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
        .filter(Transaction.date >= start, Transaction.date <= end)
        .filter(_outflow_filter())
        .filter(or_(Transaction.is_internal.is_(False), Transaction.is_internal.is_(None)))
    )
    if user_id:
        query = query.filter(Account.user_id == user_id)

Recommended resulting pattern in _next_income_date():

    query = (
        Transaction.query.join(Account, Account.account_id == Transaction.account_id)
        .filter(or_(Account.is_hidden.is_(False), Account.is_hidden.is_(None)))
        .filter(Transaction.date >= lookback, Transaction.date <= as_of)
        .filter(_inflow_filter())
        .order_by(Transaction.date.asc())
    )
    if user_id:
        query = query.filter(Account.user_id == user_id)

Do not add an unnecessary backfill migration solely to make Safe-to-Spend work.

---

## 3.4 Stop creating new Plaid transactions without user_id

File:

    backend/app/sql/account_logic.py

Current code around lines 1431-1448:

    new_txn = Transaction(
        transaction_id=txn_id,
        amount=txn_amount,
        date=txn_date,
        description=description,
        pending=pending,
        account_id=account_id,
        ...
        provider="plaid",
        ...
    )

Add:

    user_id=account.user_id,

Recommended placement:

    account_id=account_id,
    user_id=account.user_id,
    category_id=category.id,

This should match the newer ingestion implementation in:

    backend/app/services/plaid_sync.py

which already does:

    user_id=account.user_id

Do not modify plaid_sync.py unless needed for a test or shared helper. It already writes user_id correctly.

Also update existing transaction rows during refresh only if the change is safe and trivial:

    if existing_txn.user_id is None:
        existing_txn.user_id = account.user_id

This is recommended because it heals legacy null ownership opportunistically without a bulk migration.

Do not overwrite a non-null user_id.

---

## 3.5 Make deployed startup apply migrations

Existing migration:

    backend/migrations/versions/6b0f2c9d1a34_add_planning_persistence_tables.py

must be applied before the Safe-to-Spend route is considered deployable.

Docker already does this via:

    backend/docker-entrypoint.sh

Do not change the Docker migration behavior.

File:

    render.yaml

Current backend start:

    startCommand: gunicorn "backend.run:app" --bind 0.0.0.0:$PORT

This is also inconsistent with the current backend entrypoints because backend/run.py exposes main(), not a module-level app.

Use the working backend package context and run migrations before Gunicorn.

Recommended replacement:

    startCommand: cd backend && flask --app 'app:create_app' db upgrade && gunicorn wsgi:app --bind 0.0.0.0:$PORT

Do not create a new migration for the Safe-to-Spend fix.

If render.yaml is confirmed unused by the actual deployment, keep the correction anyway because it is a broken deployment definition in main, but do not make broader Render changes in this packet.

Do not change buildCommand unless tests prove it is independently broken and required for this task.

---

# 4. Backend route behavior

File:

    backend/app/routes/dashboard.py

The existing 500 response is useful:

    return jsonify({"status": "error", "message": str(exc)}), 500

Keep the response contract.

Do not replace it with a generic message before the frontend receives it.

Keep logging:

    logger.error("Failed to build safe-to-spend payload: %s", exc, exc_info=True)

If desired, make the public error slightly safer for production by mapping known schema/runtime failures to a short message, but this is optional and must not hide useful development diagnostics.

No new endpoint is required.

---

# 5. Tests

## 5.1 Extend tests/test_safe_to_spend_service.py

The current tests monkeypatch the database helpers, so they do not catch the broken SQL predicates or missing-table/runtime behavior.

Keep the existing pure calculation tests.

Add tests for provider-aware sign semantics.

Minimum cases:

### Plaid expense

Stored:

    provider="plaid"
    amount=42.50

Expected:

    counted as $42.50 spent

### Plaid income

Stored:

    provider="plaid"
    amount=-1500.00
    income metadata/category

Expected:

    eligible as income
    not counted as spend

### Non-Plaid legacy expense

Stored:

    provider="manual"
    amount=-42.50

Expected:

    counted as $42.50 spent

### Non-Plaid legacy income

Stored:

    provider="manual"
    amount=1500.00
    income metadata/category

Expected:

    eligible as income

### User scoping

Create:

- Account A with user_id=user-a
- Transaction under Account A with Transaction.user_id=None

Call with user_id=user-a.

Expected:

- transaction is included because ownership is derived through Account.

Call with user_id=user-b.

Expected:

- transaction is excluded.

Prefer testing the real query helpers against the repository's test database rather than mocking them.

---

## 5.2 Add a route/database integration test

Suggested file:

    tests/test_safe_to_spend_integration.py

or extend an existing dashboard integration suite if one already provides real SQLAlchemy fixtures.

The test must create actual:

- Account
- Transaction
- PlanningScenario
- PlannedBill

Then call:

    GET /api/dashboard/safe-to-spend

Verify:

- HTTP 200
- status == "success"
- spendable cash is populated
- planned bill is included
- Plaid outflow is included in spent_today_cents
- no ORM/schema exception occurs

This specifically prevents the existing mock-heavy tests from declaring success while production SQL fails.

Do not stub build_safe_to_spend_payload in this integration test.

---

## 5.3 Transaction ingestion regression test

Add to the closest existing account logic transaction test, preferably:

    tests/test_account_logic_transactions.py

Verify a newly created Plaid Transaction through refresh_data_for_plaid_account receives:

    transaction.user_id == account.user_id

Also verify a legacy existing transaction with user_id=None is healed to account.user_id if the opportunistic repair described above is implemented.

---

## 5.4 Frontend error propagation test

Use the existing Dashboard view test location.

Mock:

    api.fetchSafeToSpend

to reject with:

    {
      response: {
        data: {
          message: 'relation "planned_bills" does not exist'
        }
      }
    }

Expected:

- the Safe-to-Spend surface displays the backend message
- it does not reduce it to only "Unable to calculate spend room."

Also test a normal generic Error with no response payload falls back to error.message or the generic fallback.

Do not add a new global error system for this.

---

# 6. Do not modify

Unless directly required by failing tests, leave these alone:

- frontend/src/components/dashboard/SafeToSpendCard.vue
- frontend/src/services/api.js
- planning schema/models
- Plaid transaction storage sign convention
- account balance normalization
- dashboard layout/styling
- forecast engine
- transaction display-sign helpers

This packet fixes Safe-to-Spend reliability, not pyNance transaction semantics globally.

---

# 7. Expected files changed

Primary:

- frontend/src/views/Dashboard.vue
- backend/app/services/safe_to_spend.py
- backend/app/sql/account_logic.py
- render.yaml
- tests/test_safe_to_spend_service.py
- tests/test_account_logic_transactions.py

Likely new or extended integration test:

- tests/test_safe_to_spend_integration.py

Documentation:

- docs/backend/app/services/safe_to_spend.md
- docs/frontend/safe-to-spend.md

Only touch additional files when a concrete test dependency requires it.

---

# 8. Recommended implementation sequence

1. Fix provider-aware _outflow_filter / _inflow_filter in safe_to_spend.py.
2. Change Safe-to-Spend user scoping to Account.user_id.
3. Add user_id to the legacy account_logic.py Plaid Transaction constructor.
4. Opportunistically heal null existing_txn.user_id.
5. Add focused backend tests.
6. Add real DB/route integration coverage.
7. Surface backend error messages in Dashboard.vue.
8. Add frontend error test.
9. Fix render.yaml startup migration/WSGI command.
10. Update Safe-to-Spend docs.
11. Run focused tests, then full validation.

---

# 9. Acceptance criteria

- [ ] Safe-to-Spend returns 200 when the existing planning migrations have been applied.
- [ ] render.yaml applies Alembic migrations before starting the backend.
- [ ] render.yaml starts the actual WSGI app rather than backend.run:app.
- [ ] Dashboard displays a useful backend error when Safe-to-Spend returns 500.
- [ ] Plaid positive amounts count as spending.
- [ ] Plaid negative amounts can qualify as income.
- [ ] Existing non-Plaid sign behavior remains unchanged.
- [ ] Safe-to-Spend scopes transaction ownership through Account.user_id.
- [ ] A transaction with null Transaction.user_id still counts for its owning account/user.
- [ ] account_logic.py writes user_id on newly inserted Plaid transactions.
- [ ] Legacy null transaction user_id values are healed during refresh if safely implemented.
- [ ] Existing Safe-to-Spend pure calculation tests still pass.
- [ ] At least one real database-backed Safe-to-Spend route test exists.
- [ ] No duplicate planning migration is added.
- [ ] No global transaction-sign rewrite is introduced.

---

# 10. Validation commands

Backend focused:

    pytest -q tests/test_safe_to_spend_service.py
    pytest -q tests/test_safe_to_spend_integration.py
    pytest -q tests/test_account_logic_transactions.py
    pytest -q tests/test_dashboard_activity_status_route.py

Frontend focused:

    cd frontend
    npm run test -- --run

If the Dashboard tests are Cypress component tests instead of Vitest, use:

    npm run test:unit -- --spec "src/**/Dashboard*.spec.*"

Use the repository's existing test file type rather than converting test frameworks for this task.

Full validation:

    pytest -q
    cd frontend && npm run lint
    cd frontend && npm run test -- --run
    pre-commit run --all-files
    python scripts/check_docs.py --changed-since origin/main
    python scripts/doc_cleaner.py

---

# 11. Completion report required

Report:

1. files changed;
2. exact provider-aware sign predicates used;
3. whether Account.user_id replaced Transaction.user_id in both Safe-to-Spend queries;
4. whether legacy null transaction ownership is repaired;
5. whether the live/deployment migration command was corrected;
6. focused test results;
7. full validation results;
8. any deviation from this packet and why.

---

## Design lock

Safe-to-Spend must calculate against raw provider data correctly, use Account as the ownership authority, fail visibly rather than generically, and run only against an up-to-date migrated schema. Fix those seams directly. Do not broaden the task into a finance-engine rewrite.
