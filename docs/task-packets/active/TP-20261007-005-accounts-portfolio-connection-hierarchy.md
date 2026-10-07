# TP-20261007-005: Accounts Portfolio + Connection Hierarchy

**Packet ID:** TP-20261007-005  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-005-accounts-portfolio-connection-hierarchy.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-002  
**Priority:** High  
**Series:** UI/UX reauthor, packet 4 of 8  

## Objective

Reorder Accounts around the selected account's financial state and connection health. Maintenance and cross-account analytics remain available, but they should not precede the user's current balance/change context.

## Confirmed current state

File: `frontend/src/views/Accounts.vue`

The Summary tab currently leads with **Most Active Accounts**, then **Net Change Summary**, then **Balance History**, then **Manage Linked Accounts**. The page subtitle is "Link and refresh your accounts", which frames maintenance as the page's main purpose even though the page also provides financial monitoring.

The selected-account control sits in a large standalone bordered block under PageHeader, and refresh/connection actions are split across cards/sidebar.

## Target hierarchy

For a selected account:

1. account identity + balance/connection state;
2. net change KPIs;
3. balance history;
4. recent activity;
5. secondary cross-account analytics;
6. connection management.

For no selected account:

1. portfolio/account list;
2. connection actions;
3. cross-account overview.

## Required changes

### 1. Integrate account selection with page context

File: `frontend/src/views/Accounts.vue`

Move the selected account control into the page header/action region or a compact context bar immediately below it. Remove the large standalone "Viewing account" card treatment.

Update subtitle toward outcome language such as balances/activity/connection health rather than "Link and refresh".

### 2. Put current financial state first

On Summary, move `Net Change Summary` before `Most Active Accounts`.

Add a compact selected-account status line using data already present in `accounts` / `linkedAccounts`:

- display name;
- institution/mask when available;
- balance;
- connection/reconnect state when available.

Do not create a new backend endpoint.

### 3. Make connection problems actionable, not ambient

Files:

- `frontend/src/views/Accounts.vue`
- `frontend/src/components/accounts/LinkedAccountsSection.vue`
- `frontend/src/components/forms/AccountActionsSidebar.vue`

If a connection requires attention, surface one concise warning/action near the selected account context. Do not repeat the same reconnect action in multiple prominent locations.

Connection maintenance belongs in a dedicated low-priority area/tab/sidebar after the primary financial state.

### 4. Reframe tabs

Keep existing functionality, but use user-task labels and ordering. Preferred structure:

- Overview
- Activity
- Trends
- Connections

Mapping may reuse current Summary/Transactions/Charts slots internally if changing slot names would create unnecessary churn, but rendered labels should be task-oriented.

Do not exceed four primary tabs.

### 5. Demote cross-account ranking

`Most Active Accounts` is useful context, but should be a secondary portfolio insight, not the first Summary card for a selected account.

Place it below selected-account trend or in a secondary overview section. Keep count/value toggle if still useful, but reduce its visual weight.

### 6. Unify refresh behavior

Review selected-account refresh buttons and `AccountActionsSidebar`. Preserve capabilities while ensuring one obvious primary refresh action. Avoid multiple equal "Refresh" controls that appear to do slightly different things without explanation.

## Tests

Update:

- `frontend/src/views/__tests__/Accounts.spec.js`
- `frontend/src/views/__tests__/AccountsSummary.cy.js`
- `frontend/src/views/__tests__/AccountsRetry.cy.js`
- `frontend/cypress/e2e/accounts.cy.js` where relevant

Cover:

- selected-account state precedes cross-account ranking;
- connection-attention action appears only when needed;
- tab labels/order;
- account selection still drives summary/history/activity;
- refresh/reconnect behaviors remain.

## Non-goals

- Do not alter account classification or balance math.
- Do not change Plaid reconnect backend behavior.
- Do not redesign individual charts in this packet.
- Do not remove hidden/closed account support.

## Acceptance criteria

- [ ] Selected account financial state is the first substantive content.
- [ ] Most Active Accounts is secondary.
- [ ] Account selector is compact and contextually placed.
- [ ] Connection errors are actionable and non-duplicative.
- [ ] Tabs map to Overview / Activity / Trends / Connections or equivalent task language.
- [ ] No more than four primary tabs.
- [ ] One refresh path is visually primary.
- [ ] Existing account data behavior remains intact.
- [ ] Focused Accounts tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/views/__tests__/Accounts.spec.js
npm run lint
npm run build
```

## Completion report

Report new hierarchy, tab mapping, connection-health treatment, refresh action ownership, tests, and deviations.
