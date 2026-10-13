# TP-20261012-001: Link Account Modal Visibility + Overlay Readability

**Packet ID:** TP-20261012-001  
**Status:** Complete  
**Created:** 2026-10-12  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261012-001-link-account-modal-visibility.md`  
**Workstream size:** One independently testable frontend repair packet  
**Depends on:** None; coordinate with TP-20261007-005 and TP-20261007-009  
**Priority:** High  
**Issue:** User screenshot shows the Link Account selector squeezed/cropped, product-card text partially hidden, and a scrollbar inside the tiny visible portion of the dialog.

## Objective

Make the Accounts > Link Account > Choose what to sync dialog fully visible, usable, and keyboard-accessible at desktop, mobile, and short viewport heights. Repair modal containment at the source, preserve Plaid linking and product selection, and close other *proven instances of the same overlay-visibility failure* on the immediate account-linking surface. This is **not** the broader cross-app redesign.

## Confirmed current main implementation (2026-10-12)

1. `frontend/src/views/Accounts.vue` renders `TabbedPageLayout` with a fixed-width sidebar specified as `sidebar-width="w-72 md:w-80"`; its `#sidebar` slot renders `AccountActionsSidebar`.
2. `frontend/src/components/forms/AccountActionsSidebar.vue` nests `LinkAccount` inside a sidebar of roughly 18–20rem width.
3. `frontend/src/components/forms/LinkAccount.vue` renders a root `Card`, and when `showDialog` is true renders the modal **inside that Card**. Its `.link-dialog-backdrop` uses `position: fixed; inset: 0; z-index: 50`; its `.link-dialog` has `width: min(560px, 100%)`, `max-height: min(85vh, 44rem)` and `overflow-y: auto`.
4. `frontend/src/components/ui/Card.vue` wraps slot content in `class="card glass"`. The global `.glass` utility in `frontend/src/assets/css/main.css` applies `backdrop-filter: blur(8px)`. A non-none backdrop filter establishes a containing block for fixed-position descendants in conforming browsers. **Root-cause hypothesis:** fixed overlay is attached to the filtered sidebar Card's coordinate system, instead of the viewport, resulting in a constrained/clipped modal. Verify this in a real browser; do not assert success solely from code inspection.
5. `frontend/src/components/forms/PlaidProductScopeSelector.vue` renders button cards for `transactions`, `investments` and `liabilities` with controlled `modelValue` and `update:modelValue`. The visible text in the screenshot ("cash flow insights", "Investments") matches this component. The buttons are not native `<select>` options.
6. Existing component tests: `frontend/src/components/forms/__tests__/LinkAccount.cy.js` and `frontend/src/components/forms/__tests__/PlaidProductScopeSelector.cy.js`. They cover selection/launcher errors, not viewport geometry.
7. `frontend/src/components/layout/TabbedPageLayout.vue` has a fixed sidebar + `flex` layout at narrow sizes. TP-20261007-009 explicitly owns app-wide sidebar collapsing and general clipped-popover cleanup. Do not perform that redesign here unless necessary to make Link Account usable; report any remaining layout issue to 009.
8. `frontend/src/components/ui/Modal.vue` is an older shared modal with `fixed inset-0`. Inspect **only when a current consumer reproduces a similarly trapped fixed overlay**, and fix the same pattern consistently without undertaking a modal-library rewrite.

### Distinguish evidence from hypothesis

The screenshot establishes a serious visibility/scrolling defect. The filtered ancestor explains the symptom and is a high-confidence hypothesis, **not yet browser-verified**. Capture the pre-fix modal/backdrop bounding rectangles and computed ancestor styles at least once before editing, so the closeout records a true failure mechanism.

## Work boundaries and coordination

- One packet: `TP-20261012-001`; standalone, no new backend or database dependencies.
- This packet owns Link Account overlay geometry, focus/scroll behavior, selector legibility, and directly adjacent visibility regression tests.
- `TP-20261007-005` owns the broader Accounts information hierarchy, connection actions and tab structure.
- `TP-20261007-009` owns the final cross-app responsive/readability audit and `TabbedPageLayout` sidebar reflow.
- If either packet has already changed one of the named files, refresh **only the affected symbols** from current `origin/main` and preserve their changes; do not reset/recreate the old UI to match this packet's historical excerpt.
- Do not rediscover Plaid backend flows, reclassify products, redesign Dashboard, or make app-wide aesthetic changes.

## Required implementation

### 1. Fix ownership of the modal at the DOM boundary

**Primary file:** `frontend/src/components/forms/LinkAccount.vue`  
**Related:** `frontend/src/components/ui/Card.vue`, `frontend/src/assets/css/main.css` (read-only unless a truly shared fix is justified).

- Keep the "Link Account" trigger in its existing parent. Render the `v-if="showDialog"` backdrop and dialog through a Vue `<Teleport to="body">`, outside `Card.glass` / fixed sidebar / app content. Vue's template teleport is the preferred minimal solution.
- Preserve the existing fade transition, `showDialog` state, refs, handlers, two-step content, and `LinkProviderLauncher` slot semantics. Adjust transition nesting so the popup enter/leave behavior is preserved; avoid unmounting unexpectedly on button clicks.
- Maintain viewport-level `position: fixed; inset: 0` and a deliberate layer above navigation/sidebar; do **not** paper over the containing-block bug with a larger z-index or `overflow: visible` on the sidebar.
- Backdrop owns the single viewport layer and vertical scrolling; dialog uses `width: min(560px, 100%)` or equivalent, `box-sizing: border-box`, and a height strategy that remains usable in a short viewport. Avoid accidental double vertical scrollbars, inaccessible header/actions, horizontal scrolling, and scroll chaining to the underlying page.
- Ensure adequate insets on small screens, padding respecting available height, natural wrapping of helper text, and no content hidden behind borders or scrollbars. Verify real box geometry, not solely snapshots.
- If necessary use `min-height: 0` / `min-width: 0` on flex/grid descendants, `max-width: 100%`, and safe viewport dimensions (`dvh` with sensible fallback), but only at the actual pressure points.

**Suggested target structure (pseudocode, not an API change):**

    <Card>... trigger ...</Card>
    <Teleport to="body">
      <transition name="fade">
        <div v-if="showDialog" class="link-dialog-backdrop" ...>
          <div ref="dialogRef" class="link-dialog" role="dialog" ...>
            ... existing steps, scope selector, provider launcher ...
          </div>
        </div>
      </transition>
    </Teleport>

Vue SFC template restrictions and root nodes should be checked against the currently installed Vue version. Do not mount or render the Teleport outside the component state lifecycle.

### 2. Make product cards and action footer unquestionably readable

**Files:** `frontend/src/components/forms/PlaidProductScopeSelector.vue` and `frontend/src/components/forms/LinkAccount.vue`.

- Ensure all three full product labels and descriptions are visible with normal text wrapping; no ellipsis, masked side columns, or tiny nested scrollbox.
- Preserve `aria-pressed`, active appearance, contrast, and the accessible group legend. Add explicit `:focus-visible` treatment on scope buttons using existing theme focus tokens if keyboard focus is not adequately visible.
- Selection must remain controlled by `selectedProducts`; do not silently select products on opening. Keep the CTA disabled for zero products and preserve existing launcher error/retry behavior.
- Make the dialog title, step descriptions, close control, Cancel and Link actions discoverable in both themes. On short screens, scrolling **within the single expected modal scroll area** must reach the action footer.
- Do not restyle unrelated page cards or create a new design system. Follow the present Nightfox/Everforest variables and TP-20261007-002's forthcoming hierarchy roles without requiring that packet to land first.

### 3. Keyboard/focus and document-scroll lifecycle

**File:** `frontend/src/components/forms/LinkAccount.vue`.

- Open: remember opener, move focus into dialog, prevent background interaction and document scrolling.
- Tab/Shift+Tab: keep focus inside dialog, including the selector and footer; close: Escape, close button or Cancel returns focus to the opener if still connected.
- Verify backdrop-click behavior stays deliberate (`@click.self`), and an error/retry does not close the dialog or lose focus.
- Unmount while open: remove the keydown listener and restore precisely the page scroll lock this instance owns; never reset a body overflow value belonging to another still-open overlay. If other modals share the page, make ownership sufficiently safe for this component's lifecycle without inventing a global manager.
- Where appropriate, include `inert`/focus safety for background content; do not add intrusive dependencies. Ensure semantic dialog label/description refs still resolve after Teleport.

### 4. Bounded visibility audit: neighboring surfaces only

Files to *inspect*, not automatically modify:

- `frontend/src/components/layout/TabbedPageLayout.vue` and `frontend/src/views/Accounts.vue` for unintended offscreen navigation/sidebar that prevents launching the dialog.
- `frontend/src/components/forms/AccountActionsSidebar.vue` for button truncation.
- `frontend/src/components/ui/Modal.vue` for another *reproducible*, Card/filter-trapped fixed overlay consumer in the account-linking path.
- `frontend/src/components/ui/PageHeader.vue` and `frontend/src/assets/css/main.css` for theme contrast/focus impacts if discovered while testing.

Record each inspected issue as **fixed**, **not reproduced**, or **deferred to TP-20261007-005/009**. Any proven adjacent overlay defect may be fixed in this packet if it shares the same root cause and remains a small local change. Wider cross-app work must stay with 009.

## Tests and evidence

**Update:** `frontend/src/components/forms/__tests__/LinkAccount.cy.js`  
**Update:** `frontend/src/components/forms/__tests__/PlaidProductScopeSelector.cy.js`  
**Only if needed:** `frontend/cypress/e2e/accounts.cy.js` and current Accounts component tests.

- Mount the real `LinkAccount` inside a narrow Card/sidebar container with `backdrop-filter` enabled. Open and assert the backdrop is attached to `document.body` (or the intended top-level overlay layer), not inside `.glass`.
- For viewport configurations `360x640`, `390x844`, `768x1024`, `1440x900`, and a short `1280x600`, assert backdrop rectangle covers the viewport within reasonable rounding tolerance; dialog left/right edges are within viewport bounds; no unexpected document horizontal overflow; the first and last product cards are readable and the bottom actions can be scrolled into view.
- Repeat primary geometry checks in both supported app themes. Add at least one 200%-zoom/reflow or equivalent compact CSS pixel viewport check where Cypress/Playwright supports it reliably; if not, document the manual verification.
- Test keyboard Tab/Shift+Tab containment, Escape/Cancel/close button, focus return, body overflow restoration on normal close and unmount, selection toggles, empty-scope disabled CTA, and inline launcher error/retry.
- Use deterministic stubs for Plaid launcher/network. **Do not connect to real financial institutions or require live Plaid credentials** for visual testing.
- Record one before/after narrow-crop screenshot or browser measurements if test infrastructure allows, without committing secrets or large generated image artifacts. The implementation summary should state whether the filtered-ancestor hypothesis was confirmed.

### Commands

    cd frontend
    npm run test:unit -- --spec src/components/forms/__tests__/LinkAccount.cy.js
    npm run test:unit -- --spec src/components/forms/__tests__/PlaidProductScopeSelector.cy.js
    npm run lint
    npm run build
    npm run test -- --run

Adjust the Cypress `--spec` command to the actual project runner conventions if needed (the package script is `cypress run --component`). Run any targeted Accounts e2e spec only if its fixtures can be used without live provider credentials. Report command, pass/fail count, and pre-existing failures, not a blanket "tests pass."

## Non-goals

- No Plaid token, endpoint, product scope, backend, database or authentication changes.
- No rewrite of global modal infrastructure solely for abstraction.
- No forced change to the Accounts tab/sidebar hierarchy already assigned to TP-20261007-005 and 009.
- No blanket deletion of `backdrop-filter` from the theme, no arbitrary `!important` / extreme z-index workaround.
- No new dependency or full redesign of all six dashboard surfaces.
- Do not convert the buttons to a native select; the screenshot is a *broken modal containing product cards*.

## Implementation order

1. Fetch/sync `main` safely under root `AGENTS.md`; resolve packet and mark `In Progress` in packet/TRACKER.
2. Reproduce and measure the existing modal clipping inside the filtered Card.
3. Teleport modal to top-level DOM; correct scrolling/bounds and focus/scroll lifecycle.
4. Correct only necessary selector wrapping, focus visibility and action alignment.
5. Add focused viewport/interaction tests and run targeted validations.
6. Audit the bounded neighboring surfaces; explicitly defer broader issues to 005/009.
7. On success move packet to `completed/`, update `INDEX.md` and `TRACKER.md` in the same commit, publish validated changes to `origin/main` per `AGENTS.md`, verify remote head.
8. If blocked, leave packet in `active/` with `Blocked` and exact reproduction/failed command/resume condition in TRACKER; do not claim completion.

## Acceptance criteria

- [ ] Link Account modal is visible at viewport level, never confined to its sidebar Card.
- [ ] Selector's Transactions, Investments and Liabilities cards and helper text are legible and selectable.
- [ ] Header, close action, both steps, CTA, and cancel action remain reachable on short screens.
- [ ] No unintended page-horizontal scrolling or trapped nested scrollboxes at tested sizes.
- [ ] Nightfox/Everforest contrast and keyboard focus are readable.
- [ ] Escape, focus trap/return, backdrop click, and document-scroll cleanup work correctly.
- [ ] Empty-scope CTA and Plaid error/retry semantics are unchanged.
- [ ] Geometry and behavior regression tests fail on the original bug and pass after correction.
- [ ] Adjacent visibility findings are fixed within scope or clearly deferred by packet ID.
- [ ] Targeted tests, frontend lint, and build pass, or any pre-existing failures are precisely identified.
- [ ] Packet/index/tracker closeout lands on remote `main` with no unrelated changes.

## Completion report

Start with `Workstream: TP-20261012-001`. Include confirmed root cause, files changed, before/after geometry/breakpoints/themes, keyboard/accessibility checks, focused/full validation results, scoped deferrals to 005/009, final commit SHA + GitHub link, whether `origin/main` and the local checkout are synchronized, and **Authoring chat:** exact user-supplied URL when one is available (never invent one). State any blocker plainly. 

---

## Completion report (2026-10-13)

Workstream: TP-20261012-001

- **Fix:** `LinkAccount.vue` now renders the backdrop/dialog through `<Teleport to="body">`, so it is no longer a descendant of the `backdrop-filter` Card. Backdrop owns the single scroll area (`overflow-y: auto`, `overscroll-behavior: contain`); dialog has no inner `max-height`/scroll and centers via `margin: auto`. `inheritAttrs: false` + `v-bind="$attrs"` on the Card preserves the previous attr/listener fallthrough now that the root is a fragment.
- **Selector:** `PlaidProductScopeSelector.vue` gains `:focus-visible` outline and `min-width: 0` on the options grid.
- **Root cause:** filtered-ancestor hypothesis NOT browser-measured pre-fix (no before-measurements captured); the new body-attachment test encodes it and would fail on the old in-Card structure by construction.
- **Tests:** `LinkAccount.cy.js` rewritten (old spec used stale copy): CTA gating, launcher error/retry, teleport-outside-filtered-card, geometry at 360x640/390x844/768x1024/1440x900/1280x600, Escape/focus restore/body overflow, unmount-while-open. 10/10 pass. `PlaidProductScopeSelector.cy.js` (template-string mount was broken without runtime compiler) fixed + focus ring check: 1/1 pass. Not done: both themes' geometry, 200% zoom, Tab/Shift+Tab containment assertions (focus-trap code unchanged; not covered by tests).
- **Validation:** `npm run lint` 0 errors (2104 pre-existing warnings); `npm run build` OK; vitest 49 files / 206 tests pass.
- **Adjacent audit:** `TabbedPageLayout.vue`, `AccountActionsSidebar.vue`, `Modal.vue`, `PageHeader.vue` — not reproduced / not inspected in a browser; any sidebar reflow deferred to TP-20261007-005/009.
