# TP-20261013-001: Plaid Reconnect Item Deduplication + Link Session Lifecycle

**Packet ID:** TP-20261013-001  
**Status:** Complete  
**Created:** 2026-10-13  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261013-001-plaid-reconnect-item-dedup-session-lifecycle.md`  
**Workstream size:** One implementation packet  
**Depends on:** None (coordinate Settings edits with in-progress TP-20261007-009)  
**Priority:** High  
**Predecessor:** TP-20261001-001 (Complete: Plaid Item Connection Health + Reconnect UI)  
**Expected packet count/order:** One packet; backend grouping and frontend state/tests ship together.

## Objective

A user reauthenticates **once per distinct Plaid Item/connection**, never once per account held within that Item. Fix the inconsistent Accounts vs Settings/Refresh Plaid interfaces and prevent duplicate/overlapping Plaid Link launches. After one successful Item update, verify all affected accounts through server-side refresh/health before removing the reconnect warning. Separate Items at the same institution remain separate connections, with a clear, user-driven sequence of repairs.

This is a **follow-up correctness fix**, not a rewrite of the implemented Item health feature.

## Confirmed current state on main (2026-10-13)

Read these exact seams, not the entire repository:

| File | Existing symbols/behavior | Gap to close |
| --- | --- | --- |
| `frontend/src/utils/plaidConnectionStatus.js` | `normalizeConnectionStatus`, `uniqueReconnectConnections` group unhealthy account rows by `connection_status.connection_id`, falling back to `account_id`. | Reuse this grouping across both entry points; enrich mapping to incorporate refresh-error snapshots without creating duplicate Item actions. |
| `frontend/src/views/Accounts.vue` | `reconnectConnection(connection)` uses `usePlaidReconnect`, calls `api.refreshAccounts({account_ids: ...})`, reloads and rechecks persisted health. | `reconnectingId` is cleared in `finally` after the composable returns from `handler.open()`, **before** Link succeeds/exits; duplicate clicks can launch another session. |
| `frontend/src/components/accounts/LinkedAccountsSection.vue` | Renders one reconnect row per `uniqueReconnectConnections()` entry; account rows also show health. | Keep this Item-level UI, but bind the button/loading/error/exit states to the real session lifecycle. |
| `frontend/src/components/widgets/RefreshPlaidControls.vue` | Settings refresh summary is keyed/displayed by `acct.account_id`; `shouldOfferReconnect(acct)` elects a representative `reauth_account_id` per *error record*. `handlePlaidReauth(acct)` refreshes `affected_account_ids` on success. | Different errors/messages for one Item can generate multiple candidates; a clean Link exit with no message may leave `reauthingAccountId` stuck; refresh subset can omit other accounts in same connection. |
| `frontend/src/views/Settings.vue` | Mounts `RefreshPlaidControls` under connected-account maintenance. | Do not build a third reconnect path; use the same Item grouping/session handling as Accounts. |
| `frontend/src/composables/usePlaidReconnect.js` | Script-loader Promise is shared; `reconnect()` fetches a token, calls `window.Plaid.create`, then `handler.open()`. `onExit` calls `onError` **only if** Plaid supplies text. | No per-connection single-flight guard or global one-modal guard; caller's await does not represent completion; clean cancellation is not surfaced; async `onSuccess` refresh failures are not explicitly folded into completion state. |
| `backend/app/routes/accounts.py` | `_plaid_item_for_account`, `_plaid_items_for_accounts` and `_append_refresh_error`; API exposes `connection_status.connection_id`. | `_append_refresh_error` includes error **message** in its key even for `ITEM_LOGIN_REQUIRED`, so message variants for a single Item can split groups. Preserve separate Items at one institution. |
| `backend/app/routes/plaid_transactions.py` | `generate_update_link_token` accepts preferred `connection_id`, legacy `account_id`, and uses `create_update_link_token` for the resolved Item. | Preserve this API; review missing-token error branch: it logs `account.account_id` even when Item-only input leaves `account is None`. Return clean 400 rather than an accidental 500. |
| `backend/app/sql/account_logic.py` | `serialized_plaid_item_connection_status` reads `PlaidItem.last_error`; `mark_plaid_item_reauth_required`/`clear_plaid_item_reauth_required` persist Item health. | Continue using Item state as authority. Do **not** clear it merely because Link reported success. |

Existing tests: `frontend/src/composables/__tests__/usePlaidReconnect.spec.js`, `frontend/src/views/__tests__/Accounts.spec.js`, `frontend/src/components/__tests__/RefreshPlaidControls.cy.js`, `tests/test_plaid_connection_health.py`, `tests/test_api_plaid_transactions.py`.

### Critical evidence

Current `Accounts.vue`:
```js
await reconnect({
  connectionId: id,
  accountId: connection.accountId ?? connection.accounts[0]?.account_id,
  onSuccess: async () => {
    await api.refreshAccounts({
      account_ids: connection.accounts.map((account) => account.account_id),
    })
    await loadAccounts()
    // Verify persisted connection health.
  },
})
// reconnect() currently returns after handler.open(), not after Link completes.
reconnectingId.value = null
```

Current `RefreshPlaidControls.vue`:
```js
const targetAccountId =
  errorInfo.reauth_account_id || errorInfo.affected_account_ids?.[0] || acct.account_id
return acct.account_id === targetAccountId
```
This deduplicates only within a refresh error record, not reliably across records representing the same Item.

Current `_append_refresh_error`:
```python
key = (
    getattr(item, "id", None) if err_payload.get("plaid_error_code") == "ITEM_LOGIN_REQUIRED" else None,
    inst,
    err_payload.get("plaid_error_code"),
    err_payload.get("plaid_error_message"),
)
```
Message is not a stable identity for an Item.

## Locked design / data contract

1. **One Plaid Item = one reauthentication session**. The local `PlaidItem.id` exposed as `connection_id` is the stable UI key, **not** institution name or child account ID. A user with two separate Items at the same bank legitimately has two sessions, not one magic institution-wide repair.
2. Keep `GET /api/accounts/get_accounts` `connection_status` as the authoritative persisted state; use refresh-response `errors` to *enrich* actionable details, not override a subsequently healthy Item.
3. Share one reconnect coordinator (extend `usePlaidReconnect` and existing `plaidConnectionStatus.js`), with at most **one active Link modal globally**, and one pending token/Link operation per connection. A repeat request for the active connection is a no-op or joins its existing promise, never a second `/generate_update_link_token` call or `Plaid.create().open()`. Different connection attempted while Link is active must be explicitly busy, not queued for automatic popup.
4. The session lifecycle is `idle -> preparing -> open -> verifying -> completed|cancelled|failed -> idle`. An awaitable outcome (or equivalent explicit state) must settle after real Link success + requested verification, error, or **clean exit**. Cleanup must run exactly once even when `onExit` follows `onSuccess`. Do not report cancellation as success or generate scary error text for a normal close.
5. `onSuccess` means Plaid completed the update UI, **not** that pyNance is healthy. Refresh **all known accounts belonging to that connection**, reload persisted health, and retain the warning if the Item remains `reauth_required`. Network/refresh verification errors should be displayed without discarding last known server truth. Do not refresh just the representative account.
6. No auto-prompt storms, no silent invocation of additional Item Link windows, no new access tokens exchanged in update mode, no credentials or external `item_id` sent to the browser/logs.
7. `connection_id` remains preferred; `account_id` fallback remains supported for legacy records/callers. If Item identity is missing, do **not** merge separate unknown accounts just by institution name.
8. Avoid new database fields/migrations. No dependency on the separate TP-20261007-009 UI visual audit; coordinate overlapping edits to `Settings.vue` / Settings component rather than undoing another workstream's changes.

## Required changes

### 1. Connection-level grouping shared by both surfaces

**File:** `frontend/src/utils/plaidConnectionStatus.js`  
**Consumers:** `frontend/src/views/Accounts.vue`, `frontend/src/components/accounts/LinkedAccountsSection.vue`, `frontend/src/components/widgets/RefreshPlaidControls.vue`.

Retain `uniqueReconnectConnections(accounts)` compatibility. Add a focused merger/adapter if needed for live refresh errors, using each affected account's normalized `connection_status.connection_id` first, then `error.connection_id`, finally a stable account-specific legacy key. Produce one UI group per Item:

```js
{
  key: 'connection:17',
  connectionId: 17,
  accounts: [/* all loaded linked accounts with this connection_id */],
  accountIds: [/* unique IDs */],
  status: { requires_reauth: true, ... },
  errors: [/* aggregated messages if currently relevant */]
}
```

Deduplicate even if the backend returns multiple `ITEM_LOGIN_REQUIRED` messages for one Item. Split a legacy error containing accounts from *different* known Items into distinct groups. Do not group two different `connection_id` values at the same bank. Account rows can still display their individual sync errors, but the **action** appears once per Item/connection. Avoid stale refresh-only warnings that conflict with fresh healthy Item state.

### 2. Single-flight Plaid session and durable lifecycle

**File:** `frontend/src/composables/usePlaidReconnect.js`  
**Key symbols:** `loadPlaidScript`, `usePlaidReconnect`, `reconnect`.

Keep the shared CDN script loader. Introduce a single shared Link lifecycle lock/module-level coordinator, acquired **before** async script/token generation. Recommended shape (illustrative pseudocode):

```js
const key = connectionId != null
  ? `connection:${connectionId}`
  : `account:${accountId}`
if (activeSession) {
  if (activeSession.key === key) return activeSession.promise
  return { status: 'busy', activeKey: activeSession.key }
}
const session = reserveSession(key)
try {
  await loadPlaidScript()
  const payload = connectionId != null ? { connection_id: connectionId } : { account_id: accountId }
  const { link_token } = await api.generatePlaidUpdateLinkToken(payload)
  // create Link, open once, settle on success/error/clean exit
  // onSuccess awaits supplied verification callback, then completes
  // onExit with no error resolves {status: 'cancelled'}
  return await session.completion
} finally {
  releaseSessionExactlyOnce(session)
}
```

Ensure the return API is consistent for Accounts and Settings and avoids unhandled async `onSuccess` failures. Preserve caller-specific hooks or return structured results such as `{status:'verified'|'cancelled'|'failed'|'busy', message?}`. Prevent the late `onExit` from overwriting a previously successful verification. Only one user-initiated Link can be open at a time. Handle errors in script loading, token creation, `Plaid.create`, `open`, callback refresh, and exit. Clean cancellation releases busy state even when Plaid supplies no display message. Reset a failed script-loader promise so retry is possible.

### 3. Accounts UI lifecycle

**File:** `frontend/src/views/Accounts.vue`  
**Component:** `frontend/src/components/accounts/LinkedAccountsSection.vue`  
**Function:** `reconnectConnection(connection)`.

Keep button disabled/busy while token generation, Plaid Link, and post-Link verification occur. Remove the early `finally` reset tied only to `handler.open()`; consume the actual terminal session outcome. Success triggers the existing targeted refresh, `loadAccounts()`, and persisted health check. Preserve the reconnect action/status if still unhealthy. Cancellation restores idle without treating the Item as repaired. Keep the link button at the Item level, not beside each account.

### 4. Settings/Refresh Plaid UI reconciling ephemeral errors

**File:** `frontend/src/components/widgets/RefreshPlaidControls.vue`  
**Host:** `frontend/src/views/Settings.vue`.  
**Functions/computed:** `shouldOfferReconnect`, `handlePlaidReauth`, `errorByAccountId`, `targetedAccountsByInstitution`.

Keep current per-account refresh drill-down and error pills; replace representative-account action selection with a single Item-grouped reconnect action per distinct connection. Use shared coordinator and connection-key loading/message state, not `reauthingAccountId`. Use the full account/connection map returned from `api.getAccounts()` (and refresh it after Link) to obtain all known account IDs for the Item, not only `affected_account_ids` in the triggering error. Preserve legacy account fallback when Item unavailable. Cancellation resets button state. Do not blindly set UI success or hide the warning until server health is verified.

### 5. Backend refresh-error aggregation and missing-token path

**Files:** `backend/app/routes/accounts.py`, `backend/app/routes/plaid_transactions.py`.  
**Functions:** `_append_refresh_error`, `generate_update_link_token`.

For `ITEM_LOGIN_REQUIRED`, aggregate on resolved local Item ID plus error code, **excluding message**; preserve `account_ids`, `affected_account_ids`, representative `reauth_account_id` for legacy callers, and `connection_id`. Missing Item: retain account-scoped separation rather than collapsing unknown Items from the same institution. Any summary/logger that assumes the old key tuple must be adjusted. Keep non-reauth error aggregation semantics unless tests expose a concrete issue.

In `generate_update_link_token`, when only `connection_id` is supplied and that Item lacks `access_token`, return a well-defined 400 with actionable message; do not dereference `account.account_id` when `account` is `None`. Keep 404 for unknown connection and 400 for missing identifier. `connection_id` wins when both identifiers supplied; do not accidentally reject it because the account fallback was not resolved. Do not expose stored credentials.

### 6. Diagnostics and documentation

Add minimal structured diagnostics at launch/exit/verification: local connection ID, number of child account IDs, stage/outcome, and a safe failure code. No access tokens, external Plaid Item IDs, bank credentials, or full raw Plaid payloads. In application-visible copy say "Reconnect [institution]" / "X accounts affected" where truthful, distinguishing two separate bank Items when needed; avoid exposing debugging IDs as a primary UX.

Update `docs/integrations/plaid_error_remediation.md` to document one reconnect per Item, Settings/Accounts parity, clean exit/retry, multi-Item same-bank behavior, server-health verification, and legacy fallback. Keep the packet itself in the canonical task-packet system; do not create a competing task doc.

## Focused regression tests

**Frontend:** `frontend/src/composables/__tests__/usePlaidReconnect.spec.js`

- Two simultaneous clicks for one connection create **one token request / one `Plaid.create` / one `open`**, and neither session loses verification/error state.
- Another connection while Link is already active does not open a competing popup; is explicitly busy and retryable afterward.
- Opening Link without onSuccess is not completion; busy stays active until onSuccess/onExit.
- Clean `onExit(null)` settles as cancellation and releases lock. Error exit settles with message and releases lock. Cancellation never clears reconnect warning.
- A later `onExit` after `onSuccess` does not overwrite successful verification.
- Token-generation or verification rejection does not leak active state or create unhandled promises; retry succeeds.
- Legacy `account_id` and preferred `connection_id` payloads work. Shared Plaid script loads once.

**Frontend:** `frontend/src/views/__tests__/Accounts.spec.js` and `frontend/src/components/__tests__/RefreshPlaidControls.cy.js` (add Vitest component coverage if Cypress fixture is insufficient)

- One Item with checking + savings + credit displays **one** reconnect action in both Accounts and Settings, even when refresh returns different error messages for the three accounts.
- Two Items at the same institution display two distinct reconnect actions.
- A single user click initiates one Link session, not one session/account.
- After onSuccess, targeted refresh contains all loaded child accounts for the Item; status stays warning if API still reports reauth; disappears only after confirmed healthy response.
- Cancel and failed verification leave actions usable, do not falsely mark healthy, and do not leave "Opening Plaid..." stuck.
- Repeated refresh and repeated renders do not add duplicate reconnect rows.
- Legacy missing `connection_id` remains individually reconnectable, never falsely coalesced by institution alone.

**Backend:** `tests/test_plaid_connection_health.py` and `tests/test_api_plaid_transactions.py`

- `_append_refresh_error` groups same Item / different login-required messages into one actionable error with distinct affected account IDs.
- Two different Items at the same institution are not merged.
- Missing Item identity preserves safe account-based separation.
- Update-token route handles connection-only missing access token without 500; unknown Item 404, missing IDs 400, legacy account ID works, no secret fields in public response.
- Existing Item health/webhook tests remain green.

## Validation commands

Focused first (adjust working directory only for the commands that require it):

```bash
pytest tests/test_plaid_connection_health.py tests/test_api_plaid_transactions.py -q
cd frontend
npx vitest run src/composables/__tests__/usePlaidReconnect.spec.js src/views/__tests__/Accounts.spec.js
npx cypress run --component --spec "src/components/__tests__/RefreshPlaidControls.cy.js"
npm run lint
npm run build
cd ..
python scripts/check_docs.py --changed-since origin/main
```

Then run the repo's full available `pytest -q` and `cd frontend && npm run test -- --run`. Run Cypress with its necessary local dependencies; if unavailable, report precisely what blocked it and which tests were still executed. Do not claim a pass without executing a command. Docs-only authorship of this packet requires no application tests; implementation completion does.

## Implementation order / coordination

1. On latest `main`, reconfirm only the symbols listed above, `AGENTS.md`, `README.md`, and the tracker. Mark packet and tracker `In Progress`.
2. Implement shared status/error grouping + unit tests.
3. Implement shared single-flight/session outcome in `usePlaidReconnect` + unit tests.
4. Wire Accounts and Settings/Refresh controls to it; add component/interaction regressions. Coordinate overlapping `Settings.vue` work with TP-20261007-009.
5. Harden backend aggregation/update-token missing-token handling + pytest.
6. Update Plaid remediation doc, run focused/full validation, then move this packet to `completed/` and atomically update INDEX/TRACKER per AGENTS.

**Do not rediscover:** The Item model and link-token update endpoint already exist. Start with the concrete paths above; do not conduct a broad Plaid redesign or build an alternate auth framework.

## Non-goals

- No database migrations or changes to the Plaid Item vs account schema.
- No institution-name-wide merge of genuinely separate Plaid Items.
- No automatic serial relaunch of Plaid popups without a user gesture.
- No changes to unrelated account linking/onboarding, transaction categorization, investments calculations, account selector styling, or TP-20261007-009 visual redesign.
- No optimistic clearing of persisted `ITEM_LOGIN_REQUIRED`.

## Acceptance criteria

- [ ] Exactly one reconnect action/session/token request per unhealthy **Item** (not per child account) for a given deliberate user launch.
- [ ] Accounts and Settings use the same dedupe and session semantics.
- [ ] Double-clicks and concurrent requests cannot open multiple Link modals.
- [ ] Clean exit, error, success, and post-Link verification all settle and release busy state correctly.
- [ ] Targeted refresh includes all known children in the repaired Item; warning remains until server confirmation.
- [ ] Different Items at same institution remain distinct; unknown Item IDs are not guessed or merged.
- [ ] `_append_refresh_error` is stable against changing error messages for one Item.
- [ ] Connection-only missing-token case returns controlled error, not 500.
- [ ] Focused frontend/backend tests added and pass, or precise blockers recorded.
- [ ] Existing Item health and update-link legacy contracts preserved.
- [ ] Documentation updated, no secret-bearing diagnostic output.

## Completion report

Report first line `Workstream: TP-20261013-001`. Include Status, GitHub commit URL, files changed, Item/account scenarios verified, exact commands/results, any unverified browser behavior/blockers, follow-up packet (or None), and the canonical packet path. Keep the workstream in `active/` if implementation is not fully complete and validated. Do not fabricate an authoring-chat URL.

---

## Completion report (2026-10-13)

Workstream: TP-20261013-001
Status: Complete

**Changed**
- Backend: `_append_refresh_error` (`backend/app/routes/accounts.py`) aggregates `ITEM_LOGIN_REQUIRED` by Item and code (message excluded), de-duplicates account IDs, and keeps Item-less accounts account-scoped. `generate_update_link_token` (`backend/app/routes/plaid_transactions.py`) returns a controlled 400 for a connection with no access token (no `account.account_id` dereference) and no longer 404s when `connection_id` and an unresolved `account_id` are both sent.
- Frontend: `reconnectConnectionGroups` in `plaidConnectionStatus.js` (one group per Item, persisted health beats stale refresh errors); `usePlaidReconnect` rewritten as an app-wide single-flight coordinator resolving `verified|cancelled|failed|busy`; Accounts and Settings (`RefreshPlaidControls.vue`) now share it with one Item-level action, "N accounts affected" copy, full-Item refresh and persisted-health verification.
- `Button.vue` now declares `emits: ['click']`. Previously a parent `@click` ran twice (fall-through plus `$emit`), which also kept the Settings "All Linked Accounts" dropdown from ever opening.
- Docs: `docs/integrations/plaid_error_remediation.md`.

**Verified (commands run)**
- `.venv/bin/python -m pytest tests/test_plaid_connection_health.py tests/test_api_plaid_transactions.py` → 22 passed (5 new).
- `npx vitest run` → 51 files, 249 tests passed (new: lifecycle/grouping in `usePlaidReconnect.spec.js`, 6 Accounts lifecycle tests, new `RefreshPlaidControls.spec.js`).
- `npx cypress run --component --spec src/components/__tests__/RefreshPlaidControls.cy.js` → 3 passing (fixed its stale `/accounts/...` intercept globs and missing `click-outside` directive; added a one-Item test).
- `npx vite build` OK. `eslint`: only 2 pre-existing errors in files not touched.

**Not verified / caveats**
- No real Plaid Link run (needs live credentials and a browser); behavior verified against a fake `window.Plaid`.
- Full `pytest -q` cannot collect (8 pre-existing module-stub collection errors, identical with and without this change). Run per file, the only failures (account_history, refresh_dispatcher, institutions, investments_routes, internal_transfer, model_deletion, model_field_validation, routes_recurring) are identical on a clean checkout.
- `check_docs.py` reported no Python/Vue files to verify.

**Follow-up:** None.
