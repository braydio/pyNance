ATTENTION CODEX - PLEASE DO THE FOLLOWING - NO NEED TO REQUEST CONFIRMATION
Delete this document once all of the below are completed.
CHECK IF THESE ARE IMPLEMENTED AND PLEASE DELETE THIS
-- Brayden, 11-30-2025 5:35 AM

---

Document
AccountSnapshotWidget - Suggested Fix Order (one at a time)

1. Fix AccountSnapshot duplicate aria-label so specs parse.
2. Patch useAccountGroups test mock to initialize DEFAULT_ACCENT (or import after mock) so suite
   runs.
3. Stabilize TopAccountSnapshot specs by ensuring mocks provide groups/accounts and stubbing network
   calls to avoid jsdom XHR noise.
4. Stub /api/accounts/get_accounts in PlanningSummary test to supply account names.
5. Guard UpdateTransactionsTable category sort when category tree is missing.
6. Add jsdom env or DOM shim to BillForm/Allocator tests.
7. Update Transactions view tests/mocks to drive loading/error states as expected.
8. Refresh Accounts view snapshot (or match without data-v attributes).
