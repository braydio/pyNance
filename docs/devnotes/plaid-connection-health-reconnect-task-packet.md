# Task Packet: Plaid Item Connection Health + Reconnect UI

**Date:** 2026-10-01  
**Status:** Ready to implement  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Workstream size:** One implementation packet  
**Primary objective:** Make a Plaid connection that requires a fresh login persistently visible and directly repairable in the UI without requiring the user to manually trigger another refresh first.

---

## 1. Executive directive

Implement a durable Plaid connection-health flow centered on the Plaid Item, not on individual accounts.

The finished behavior must be:

1. Plaid reports ITEM_LOGIN_REQUIRED through an API failure or ITEM:ERROR webhook.
2. pyNance persists that condition at the PlaidItem level.
3. Every account API response associated with that Item exposes a normalized connection_status object.
4. The Accounts UI visibly marks the affected connection and offers one reconnect action per Plaid Item.
5. The reconnect action launches Plaid Link in update mode using the existing update-link-token backend flow.
6. Successful completion of Link is not enough by itself to clear the warning.
7. The warning clears only after pyNance verifies the Item is healthy through a successful Plaid-backed refresh, or after Plaid sends LOGIN_REPAIRED.
8. Dashboard and Settings consume the same persisted backend state rather than depending only on an error returned by the current browser session.

Do not build a second reconnect system. Reuse the current update-mode endpoint and the working Plaid Link flow already present in RefreshPlaidControls.vue.

---

## 2. Problem being fixed

The repository already detects ITEM_LOGIN_REQUIRED and already has a working Link update-mode reconnect path, but the state is fragmented.

Current behavior:

- backend/app/sql/account_logic.py converts ITEM_LOGIN_REQUIRED to a reauth_required refresh status.
- mark_plaid_item_reauth_required currently mirrors the Item-level condition onto PlaidAccount.last_error rows.
- backend/app/routes/accounts.py returns refresh_status for each account.
- frontend/src/components/widgets/RefreshPlaidControls.vue can detect requires_reauth from a refresh response and launch Plaid update mode.
- frontend/src/views/Dashboard.vue only notices reconnect requirements after its own refreshAccounts call.
- frontend/src/views/Accounts.vue drops refresh_status while remapping account objects, so the primary account-management page can be unaware that the backend already knows a login is required.
- backend/app/routes/plaid_webhook.py logs ITEM webhooks but does not currently convert ITEM:ERROR / LOGIN_REPAIRED into persistent connection-health state.

The result is a visibility gap: a Plaid Item can already be known unhealthy by the backend while the normal account UI still appears healthy.

---

## 3. Architectural locks

These are implementation requirements, not suggestions.

### 3.1 PlaidItem owns connection health

Plaid authentication is Item-scoped. A single Item can back multiple checking, savings, credit, or investment accounts.

Use PlaidItem.last_error as the persisted source for current Item-level connection trouble.

Do not introduce a new database column or migration for this packet. PlaidItem.last_error already exists.

PlaidAccount.last_error remains the account-level refresh/sync status surface. It may record that an account refresh failed, but the frontend must not use it as the authoritative source for whether a Plaid login needs repair.

### 3.2 Do not expose Plaid secrets or external Item identifiers

The browser must never receive:

- access_token
- Plaid secret values
- any other credential material

Do not require the frontend to reason about Plaid item_id.

Expose the local PlaidItem.id as connection_id.

### 3.3 One repair action per Item

If one Item backs three accounts, render one reconnect action for that Item.

Individual account rows may show that they inherit the connection problem, but do not render three independent Plaid login buttons for the same Item.

Do not assume institution name uniquely identifies an Item. A user can have more than one Item at the same institution.

### 3.4 Persisted server state drives UI state

The UI must be able to show reconnect-required immediately after loading account data.

It must not depend on the current browser session being the one that encountered ITEM_LOGIN_REQUIRED.

### 3.5 Never clear reconnect state optimistically

Plaid Link onSuccess means the update flow completed, not that pyNance has independently verified a healthy data path.

After Link onSuccess:

- perform a targeted server refresh for the accounts belonging to the repaired connection;
- reload account connection health;
- clear the UI warning only when the server no longer reports reauth_required.

LOGIN_REPAIRED is also authoritative and may clear the warning because Plaid explicitly reports that the Item healed.

### 3.6 Keep the existing update-token contract backward compatible

POST /api/plaid/transactions/generate_update_link_token currently accepts account_id.

Extend it to accept connection_id as the preferred Item-scoped identifier, while retaining account_id support for existing callers and tests.

Do not remove account_id compatibility in this packet.

---

## 4. External Plaid behavior contract

Use the current Plaid contract as the behavioral reference:

- Update mode: https://plaid.com/docs/link/update-mode/
- Item webhooks: https://plaid.com/docs/api/items/
- Item errors: https://plaid.com/docs/errors/item/

Required events for this packet:

### ITEM:ERROR

When webhook_type is ITEM and webhook_code is ERROR:

- inspect payload.error.error_code;
- when it equals ITEM_LOGIN_REQUIRED, persist reauth_required on the matching PlaidItem;
- do not treat this as an infrastructure failure;
- retain the error code/message/reason needed for diagnostics.

### ITEM:LOGIN_REPAIRED

When webhook_type is ITEM and webhook_code is LOGIN_REPAIRED:

- clear only the persisted reconnect-required condition for that Item;
- do not mutate transaction history or fabricate a successful account refresh timestamp.

PENDING_DISCONNECT and PENDING_EXPIRATION are useful future proactive warnings, but they are not required for completion of this packet. Do not broaden this implementation into a full consent-expiration system unless doing so is trivial and fully tested.

---

## 5. Backend normalized connection contract

Add a normalized connection_status object to Plaid-linked account serialization.

For a healthy Plaid Item:

    {
      "provider": "plaid",
      "state": "healthy",
      "requires_reauth": false,
      "connection_id": 17,
      "code": null,
      "message": null,
      "updated_at": "..."
    }

For ITEM_LOGIN_REQUIRED:

    {
      "provider": "plaid",
      "state": "reauth_required",
      "requires_reauth": true,
      "connection_id": 17,
      "code": "ITEM_LOGIN_REQUIRED",
      "message": "...",
      "updated_at": "..."
    }

For a non-Plaid account, connection_status may be null.

The public account payload must keep existing refresh_status, refresh_stale, and refresh_cooldown_until fields. connection_status is additive and semantically separate.

Do not rename refresh_status as part of this packet.

---

## 6. Required backend work

### 6.1 backend/app/sql/account_logic.py

Add Item-level connection-health helpers.

Required capabilities:

1. Resolve a PlaidItem from:
   - local PlaidItem.id where available;
   - Plaid item_id for webhook handling;
   - access_token for existing refresh paths.
2. Parse PlaidItem.last_error safely.
3. Serialize a normalized connection status.
4. Persist ITEM_LOGIN_REQUIRED as Item-level reauth_required.
5. Clear only a persisted reauth-required condition without deleting unrelated future Item errors.
6. Preserve existing account-level refresh helpers.

Recommended symbols:

- serialized_plaid_item_connection_status(plaid_item)
- mark_plaid_item_reauth_required(...)
- clear_plaid_item_reauth_required(...)

The exact private helper names may differ, but the public behavior must remain clear and centralized.

Update the existing mark_plaid_item_reauth_required implementation. It currently finds all PlaidAccount rows for the Item and stores reauth_required in each PlaidAccount.last_error. Change the authoritative persistence target to PlaidItem.last_error.

For backward compatibility with old rows already containing ITEM_LOGIN_REQUIRED in PlaidAccount.last_error:

- when an Item is verified healthy, clear stale account-level reauth statuses only when their parsed status is reauth_required or their code is ITEM_LOGIN_REQUIRED;
- do not erase unrelated account refresh errors.

When build_refresh_failure_status or refresh_data_for_plaid_account encounters ITEM_LOGIN_REQUIRED after a product call, make sure the Item-level helper is invoked. Do not rely solely on the initial accounts/get Plaid call catching the condition.

### 6.2 Healthy-state verification

A successful authenticated Plaid data call may clear an existing reauth_required Item state.

Implement this in a centralized way so all normal sync paths do not need bespoke cleanup.

Acceptable approaches:

- clear the Item reauth state from mark_refresh_success when the PlaidAccount identifies the Item; or
- clear it immediately after a verified successful Plaid call in the refresh orchestration.

Whichever route is chosen:

- clear only reauth_required / ITEM_LOGIN_REQUIRED;
- do not blindly null arbitrary future Item warnings;
- do not advance last_refreshed unless a real refresh already warrants doing so.

### 6.3 backend/app/routes/plaid_webhook.py

Add explicit ITEM webhook handling before the generic ignored fallback.

For ITEM + ERROR:

1. Require item_id.
2. Read payload.error.
3. If error_code == ITEM_LOGIN_REQUIRED:
   - persist Item reauth_required;
   - include error_code, error_message, error_code_reason when present;
   - commit once;
   - return a normal handled response.
4. For other Item errors:
   - keep current logging behavior;
   - do not accidentally mark them as login-required.

For ITEM + LOGIN_REPAIRED:

1. Require item_id.
2. clear_plaid_item_reauth_required for that Item;
3. return a handled response.

Do not trigger transaction sync merely because LOGIN_REPAIRED arrived.

Keep webhook signature validation and PlaidWebhookLog persistence unchanged.

### 6.4 backend/app/routes/accounts.py

Enhance GET /api/accounts/get_accounts.

Build efficient PlaidItem lookup maps once per request rather than issuing a new PlaidItem query for every account.

Resolve the Item using this order:

1. PlaidAccount.plaid_item_id
2. legacy PlaidAccount.item_id
3. legacy PlaidAccount.access_token

Attach connection_status to each Plaid-linked account using the normalized helper.

Also attach connection_status to GET /api/accounts/refresh_status so both account-status APIs agree.

Do not expose item_id or access_token.

### 6.5 Bulk refresh error aggregation

Review _append_refresh_error.

Today the aggregation key is institution + Plaid error code + message. That can collapse two separate Items at the same institution into one reconnect error.

For ITEM_LOGIN_REQUIRED:

- scope aggregation by connection identity as well as error type;
- include connection_id when resolvable;
- preserve affected_account_ids;
- preserve a representative reauth_account_id for legacy clients;
- keep requires_reauth: true;
- keep update_link_token_endpoint for compatibility.

Non-reauth errors may retain the existing institution/error grouping.

Update the bulk error-summary logging code so it does not assume every error_map key has exactly the old three-element tuple shape.

Do not introduce repeated reconnect errors for each account under one Item.

### 6.6 Single-account refresh behavior

Keep the existing successful HTTP shape for reauthentication-required cases unless tests prove a cleanup is safe.

The important requirement is that detecting ITEM_LOGIN_REQUIRED during a single-account refresh persists the Item-level state before returning.

### 6.7 backend/app/routes/plaid_transactions.py

Extend POST /generate_update_link_token.

Accepted input:

    { "connection_id": 17 }

or legacy:

    { "account_id": "..." }

Resolution order:

1. If connection_id is supplied, resolve PlaidItem directly by local database id.
2. Otherwise use the existing account_id resolver and derive its Item/access token.
3. Generate the update-mode link token from the resolved Item access token.
4. Return connection_id in the successful response when known.
5. Keep account_id in the response when an account was the input or can be safely derived.

Do not return Plaid item_id or access_token.

Error responses must distinguish:

- missing identifier;
- unknown connection/account;
- account not linked to Plaid;
- Plaid API failure.

Existing account_id callers must continue to work.

---

## 7. Frontend shared reconnect flow

### 7.1 New composable: frontend/src/composables/usePlaidReconnect.js

Move the reusable reconnect mechanics out of RefreshPlaidControls.vue.

The composable should own:

- one module-level Plaid script loader promise;
- loading/open state keyed by connection;
- current reconnect message/error;
- creation of the Plaid Link update-mode handler;
- calling api.generatePlaidUpdateLinkToken;
- onSuccess callback handoff;
- onExit error normalization.

Suggested public surface:

    const {
      reconnectingConnectionId,
      reconnectMessage,
      reconnectPlaidConnection,
    } = usePlaidReconnect()

reconnectPlaidConnection should accept enough information to support both contracts:

    {
      connectionId,
      accountId,
      onSuccess
    }

Prefer connectionId. Fall back to accountId only when connectionId is unavailable.

Do not duplicate the Plaid CDN loader in multiple Vue components after this change.

### 7.2 New connection-state utility

Add a small frontend utility or composable for normalization/deduplication rather than duplicating Map logic across Accounts.vue and Dashboard.vue.

Suggested location:

frontend/src/utils/plaidConnectionStatus.js

Required operations:

- normalize account.connection_status;
- collect one issue per connection_id;
- retain institution name;
- retain all affected account ids;
- retain one representative account id for legacy fallback;
- ignore healthy and non-Plaid accounts.

If connection_id is absent on legacy payloads, use a stable fallback key based on account_id only so the UI remains usable.

---

## 8. Accounts page: primary repair surface

### 8.1 frontend/src/views/Accounts.vue

Do not drop connection state during linkedAccounts mapping.

Carry through at minimum:

- linkType
- refreshStatus
- connectionStatus

Load accounts on mount as today.

Compute active Plaid connection issues from the persisted account payload.

When an issue exists, the normal Accounts page must expose it without requiring the user to press Refresh first.

Connect the page to usePlaidReconnect.

After Plaid Link onSuccess:

1. call api.refreshAccounts with the affected account ids for that connection;
2. call loadAccounts again;
3. verify the reloaded connection_status no longer reports reauth_required;
4. only then show success/clear the reconnect treatment;
5. if the server still reports reauth_required, keep the warning visible and show a non-destructive retry/error message.

Do not refresh every account in the system when the repaired Item's affected account ids are known.

### 8.2 frontend/src/components/accounts/LinkedAccountsSection.vue

Render connection health in the existing linked-account presentation.

Requirements:

- account rows associated with a broken Item visibly show that connection attention is required;
- render one Reconnect with Plaid action per distinct connection_id;
- do not use institution name as the dedupe key;
- continue grouping the account presentation by the existing type/institution hierarchy;
- do not restructure unrelated Rewards & Promotions behavior.

Recommended copy:

Heading/badge:
Connection needs attention

Body:
Sign in again with <institution> to resume Plaid updates.

Action:
Reconnect with Plaid

Do not show the raw Plaid error message as the primary user-facing text. It may be included in expandable details for diagnostics.

Use existing components and Tailwind/theme tokens. Do not perform a general visual redesign.

Prefer emitting a reconnect event to Accounts.vue rather than embedding a second copy of reconnect orchestration inside LinkedAccountsSection.vue.

---

## 9. Settings: reuse the shared flow

### frontend/src/components/widgets/RefreshPlaidControls.vue

Keep the existing refresh-result drilldown.

Replace its local Plaid script loading and handlePlaidReauth implementation with usePlaidReconnect.

The existing reconnect button must keep working for an ITEM_LOGIN_REQUIRED returned by the current refresh call.

When the refresh error contains connection_id, pass it to the composable.

When only reauth_account_id / affected_account_ids are available, use the legacy accountId fallback.

After successful Link completion, run the existing refresh behavior and then reload account state.

Do not preserve two independent implementations of Plaid Link update mode.

---

## 10. Dashboard: persistent warning, not session-only warning

### frontend/src/views/Dashboard.vue

The current maybeAutoSyncAccounts logic only sets accountReconnectMessage when the current refresh response contains requires_reauth.

Change the dashboard warning source so persisted connection state is also checked.

Add a lightweight account-health load using api.getAccounts, either:

- during initial dashboard load; or
- as a separate Promise.allSettled-safe request.

Set accountReconnectMessage from normalized persisted connection issues.

The warning should survive:

- page reload;
- skipped auto-sync because the localStorage interval has not elapsed;
- an ITEM:ERROR webhook received before the current browser session.

Keep the dashboard warning informational. The Accounts page is the primary repair surface.

Recommended copy:

One linked account connection needs attention. Open Accounts to reconnect it with Plaid.

Use the actual count for multiple Items.

Do not claim that an institution is repaired until persisted server state says so.

---

## 11. API service changes

### frontend/src/services/api.js

Keep generatePlaidUpdateLinkToken, but allow callers to pass connection_id.

No new HTTP client is needed.

If a targeted account refresh helper improves readability, add it here rather than issuing raw axios calls from components.

Do not modify frontend/src/api/accounts_link.js unless implementation proves it is part of the active reconnect path. Avoid duplicate API abstractions.

---

## 12. Tests

This packet is not complete without backend and frontend coverage.

### 12.1 Backend tests

Add or extend tests covering all of the following.

#### Item status persistence

- ITEM_LOGIN_REQUIRED persists to PlaidItem.last_error.
- serialized Item state returns state=reauth_required and requires_reauth=true.
- healthy Item serialization returns state=healthy.
- unrelated PlaidAccount.last_error content is not erased when clearing Item reauth.
- legacy account-level ITEM_LOGIN_REQUIRED is cleared only when the matching Item is verified healthy.

Suggested new file:

tests/test_plaid_connection_health.py

#### Account API

GET /api/accounts/get_accounts:

- Plaid account with healthy Item returns healthy connection_status.
- multiple accounts sharing one Item return the same connection_id.
- broken Item returns reauth_required on all associated accounts.
- non-Plaid account has null connection_status.
- access_token and Plaid item_id do not appear in the public payload.

GET /api/accounts/refresh_status should expose equivalent connection_status.

#### Bulk refresh

- multiple accounts under one failing Item produce one logical reconnect error.
- two separate Items at the same institution do not collapse into one error.
- reconnect errors include connection_id, affected_account_ids, requires_reauth.
- non-login errors retain existing aggregation behavior.

#### Webhooks

ITEM:ERROR with ITEM_LOGIN_REQUIRED:

- persists the Item status;
- leaves transaction sync untouched;
- returns handled 200 behavior.

ITEM:LOGIN_REPAIRED:

- clears reauth-required Item state;
- does not fabricate last_refreshed;
- does not clear unrelated error data.

Add these to the existing webhook test location if one exists; otherwise keep them in test_plaid_connection_health.py.

#### Update link token endpoint

Update tests/test_api_plaid_transactions.py:

- connection_id generates an update token.
- legacy account_id still generates an update token.
- invalid connection_id returns a clear 404-style response.
- missing both identifiers returns 400.
- response never exposes access_token or external item_id.

### 12.2 Frontend tests

#### frontend/src/composables/__tests__/usePlaidReconnect.spec.js

Mock window.Plaid and API calls.

Cover:

- connection_id preferred over account_id;
- account_id fallback;
- script loaded once;
- onSuccess callback fires;
- onExit surfaces Plaid error display text when present;
- failure to generate token does not call Plaid.create.

#### frontend/src/views/__tests__/Accounts.spec.js

Cover:

- persisted reauth_required renders on initial account load without a refresh click;
- multiple accounts sharing a connection render one reconnect CTA;
- two connection ids at one institution render two logical repair entries;
- Link success triggers targeted refresh and account reload;
- banner remains when reload still reports reauth_required;
- warning disappears only when server state becomes healthy.

#### frontend/src/components/__tests__/RefreshPlaidControls.cy.js

Update existing reconnect tests to verify the shared composable/connection_id path while preserving legacy account-id behavior.

#### Dashboard tests

Add to the existing Dashboard test file if present.

Cover:

- persisted account health sets reconnect message even when auto-sync is skipped;
- healthy connections do not show reconnect warning;
- multiple unhealthy Items produce the correct count.

---

## 13. Documentation updates required with implementation

Update these docs when code lands:

- docs/integrations/plaid_error_remediation.md
  - document PlaidItem as source of connection health;
  - document connection_status response shape;
  - document the connection_id update-token request;
  - remove language implying refresh-response-only detection.

- docs/backend/app/routes/plaid_webhook.md
  - add ITEM:ERROR ITEM_LOGIN_REQUIRED handling;
  - add ITEM:LOGIN_REPAIRED handling.

- docs/backend/api-reference.md
  - document account connection_status;
  - document connection_id support on generate_update_link_token.

- docs/frontend/accounts-component-spec.md
  - document reconnect-required presentation and one-action-per-Item rule.

Run the repository documentation guard and index generator after documentation changes.

---

## 14. Expected file set

Expected existing files to modify:

- backend/app/sql/account_logic.py
- backend/app/routes/accounts.py
- backend/app/routes/plaid_transactions.py
- backend/app/routes/plaid_webhook.py
- frontend/src/services/api.js
- frontend/src/views/Accounts.vue
- frontend/src/views/Dashboard.vue
- frontend/src/components/accounts/LinkedAccountsSection.vue
- frontend/src/components/widgets/RefreshPlaidControls.vue
- frontend/src/views/__tests__/Accounts.spec.js
- frontend/src/components/__tests__/RefreshPlaidControls.cy.js
- tests/test_api_plaid_transactions.py
- docs/integrations/plaid_error_remediation.md
- docs/backend/app/routes/plaid_webhook.md
- docs/backend/api-reference.md
- docs/frontend/accounts-component-spec.md

Expected new files:

- frontend/src/composables/usePlaidReconnect.js
- frontend/src/composables/__tests__/usePlaidReconnect.spec.js
- frontend/src/utils/plaidConnectionStatus.js
- tests/test_plaid_connection_health.py

The implementer may reuse an existing utility/test file instead of creating one of the proposed new files when that is cleaner, but must not duplicate logic merely to match this list.

No database migration is expected.

---

## 15. Non-goals

Do not expand this packet into:

- Plaid institution relinking from scratch;
- replacement of Plaid Link;
- duplicate Item cleanup;
- general account-authentication redesign;
- notification email/SMS;
- full PENDING_DISCONNECT / PENDING_EXPIRATION consent UX;
- broad Accounts page redesign;
- rewards/promotions refactor;
- transaction-sync architecture rewrite;
- removal of legacy PlaidAccount token fields;
- new authentication or authorization system.

Keep this work narrowly focused on durable, Item-scoped reconnect detection and repair.

---

## 16. Acceptance criteria

The work is done only when all of the following are true.

- [ ] A Plaid ITEM_LOGIN_REQUIRED condition is persisted on PlaidItem.
- [ ] GET /api/accounts/get_accounts exposes connection_status without leaking Plaid credentials or external item_id.
- [ ] The Accounts page shows the problem immediately from persisted state.
- [ ] Accounts.vue no longer drops connection health during mapping.
- [ ] One Plaid Item produces one reconnect CTA even when it owns multiple accounts.
- [ ] Two Items at the same institution remain independently repairable.
- [ ] Reconnect launches Plaid Link update mode.
- [ ] The update-token endpoint accepts connection_id and remains backward compatible with account_id.
- [ ] Link onSuccess does not optimistically erase server reconnect state.
- [ ] A targeted successful refresh clears ITEM_LOGIN_REQUIRED state.
- [ ] ITEM:LOGIN_REPAIRED clears ITEM_LOGIN_REQUIRED state.
- [ ] Dashboard can warn from persisted state even when auto-sync does not run.
- [ ] RefreshPlaidControls uses the shared reconnect implementation.
- [ ] Backend tests cover Item status, webhook handling, API serialization, aggregation, and token generation.
- [ ] Frontend tests cover persisted rendering, Item dedupe, reconnect flow, and verified clearing.
- [ ] Matching docs are updated.
- [ ] No database migration is introduced unless the implementer discovers a concrete schema blocker and documents why.
- [ ] No access token or other credential is exposed in API responses or logs added by this work.

---

## 17. Validation commands

Run focused validation while implementing:

    pytest -q tests/test_plaid_connection_health.py
    pytest -q tests/test_api_plaid_transactions.py

Run relevant frontend tests using the repository's configured test runner:

    cd frontend
    npm run test -- --run src/composables/__tests__/usePlaidReconnect.spec.js
    npm run test -- --run src/views/__tests__/Accounts.spec.js

Also run the existing RefreshPlaidControls and Dashboard tests using the project's supported command.

Before declaring complete:

    pytest -q
    cd frontend && npm run lint
    cd frontend && npm run test -- --run
    pre-commit run --all-files
    python scripts/check_docs.py --changed-since origin/main
    python scripts/doc_cleaner.py

If the local frontend test script uses a different Vitest/Cypress invocation, use the package.json-defined command rather than inventing a parallel runner.

---

## 18. Implementation order

Use this order to minimize drift and keep every stage testable.

1. Add Item-level status helpers and tests.
2. Add account API connection_status serialization and tests.
3. Fix bulk refresh reauth aggregation to be Item-aware.
4. Add ITEM webhook persistence/repair handling.
5. Extend update-link-token endpoint with connection_id compatibility.
6. Add shared frontend status utility.
7. Add usePlaidReconnect and tests.
8. Wire Accounts.vue + LinkedAccountsSection.vue as the primary reconnect UI.
9. Refactor RefreshPlaidControls to the shared reconnect flow.
10. Make Dashboard read persisted health.
11. Run focused tests.
12. Update documentation.
13. Run full validation.

Do not begin with cosmetic UI work. The backend state contract must be reliable first.

---

## 19. Completion report expected from the implementing agent

When this packet is finished, report:

1. files changed;
2. exact normalized connection_status contract implemented;
3. how Item status is set and cleared;
4. how duplicate accounts under one Item are deduplicated;
5. whether any legacy account-level reauth state remains and why;
6. tests added/updated;
7. focused test results;
8. full validation results;
9. any intentional deviations from this packet.

If a requirement cannot be completed, leave the repository in a passing state and call out the exact blocker. Do not silently substitute a weaker session-only warning.

---

## Design lock summary

Plaid Item owns reconnect health. Accounts inherit it. Persisted backend state drives the UI. Reconnect happens once per Item through Link update mode. Link completion alone never erases the warning; verified backend health does.
