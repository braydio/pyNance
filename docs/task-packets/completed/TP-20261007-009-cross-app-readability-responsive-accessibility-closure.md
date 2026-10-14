# TP-20261007-009: Cross-App Readability + Responsive + Accessibility Closure

**Packet ID:** TP-20261007-009  
**Status:** Complete  
**Created:** 2026-10-07  
**Last updated:** 2026-10-13  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/completed/TP-20261007-009-cross-app-readability-responsive-accessibility-closure.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-003, TP-20261007-004, TP-20261007-005, TP-20261007-006, TP-20261007-007, TP-20261007-008  
**Priority:** Normal  
**Series:** UI/UX reauthor, packet 8 of 8  

## Objective

Perform the final whole-app visual coherence pass after the major surface reauthors land. Close remaining readability, hierarchy, responsive, keyboard, and secondary-surface inconsistencies without reopening product architecture.

## Scope

Primary verification surfaces:

- Dashboard
- Accounts
- Transactions
- Forecast
- Planning
- Investments

Secondary cleanup surfaces:

- `frontend/src/views/Settings.vue`
- `frontend/src/views/Institutions.vue`
- `frontend/src/views/FinancialSummaryDetailed.vue`
- `frontend/src/views/RsaMonitor.vue`
- `frontend/src/components/layout/AppFooter.vue`
- shared tables, modals, empty/error states touched by prior packets

## Required changes

### 1. Enforce the hierarchy contract

Use `docs/frontend/PRODUCT_UI_HIERARCHY.md` from TP-20261007-002 as the audit checklist.

For every scoped view confirm:

- one clear primary surface;
- action-needed information precedes exploratory detail;
- primary/normal/quiet surface roles are used consistently;
- gradients/glows are not decorating routine utility panels;
- body copy is readable and not unnecessarily uppercase/monospaced;
- explanatory paragraphs are short and attached to a user decision.

### 2. Reconcile secondary views

#### Settings

File: `frontend/src/views/Settings.vue`

Group into clear priorities:

1. Appearance
2. AI / integration preferences
3. Connected-account maintenance
4. Advanced/local commands

The current generic `Command` executor is an advanced/admin capability. Place it behind an explicit Advanced disclosure or section so it does not compete with normal preferences.

#### Financial Summary

File: `frontend/src/views/FinancialSummaryDetailed.vue`

Add normal page identity/header and ensure date controls belong to the analysis they affect.

#### Institutions / RsaMonitor

Keep technical/admin tools functional but visually consistent. If a surface is developer/operator-oriented, label it as such rather than styling it like a consumer finance destination.

Do not promote these routes into primary navigation.

### 3. Responsive audit at real breakpoints

Validate at minimum around:

- 360px
- 768px
- 1024px
- 1440px

Fix:

- horizontal page overflow;
- stacked action bars with poor order;
- filters wider than viewport;
- tables forcing unrelated page chrome offscreen;
- clipped popovers/modals;
- oversized headers;
- sidebars that remain fixed-width on narrow screens.

`TabbedPageLayout.vue` must stack/collapse its optional sidebar rather than preserving a fixed `w-64/w-80` beside narrow content.

### 4. Keyboard and focus audit

Verify:

- logical tab order follows visual order;
- all disclosures/tabs/buttons are reachable;
- focus-visible is obvious in both themes;
- modal close/primary actions are keyboard reachable;
- no clickable `div`/row lacks keyboard semantics where row interaction remains;
- selected tabs and toggles expose appropriate `aria-selected` / `aria-pressed` semantics.

### 5. Heading/readability audit

Across scoped views:

- exactly one page-level `h1`;
- major sections use `h2`;
- subpanels use `h3`;
- avoid heading styles used solely for decoration;
- long explanatory copy uses readable line-height and reasonable measure;
- numerical values are visually aligned and not buried in paragraph text.

### 6. State consistency

Loading, empty, error, reconnect-needed, no-data, and disabled states should share the same visual grammar:

- short state headline;
- one sentence of meaning;
- one action when actionable;
- no giant empty card solely to say nothing exists.

### 7. Test/cleanup obsolete UI code

After prior packets, remove truly unused UI state/classes/components only when references prove they are dead. Do not perform broad unrelated cleanup.

## Tests and validation

Run the full frontend suite plus existing Cypress targets for the primary views.

```bash
cd frontend
npm run test -- --run
npm run lint
npm run build
```

Run available targeted Cypress specs for Dashboard, Accounts, Transactions, and Planning.

Add focused tests for:

- TabbedPageLayout narrow layout;
- Settings Advanced disclosure;
- keyboard semantics changed in this packet.

Also run:

```bash
python scripts/check_docs.py --changed-since origin/main
python scripts/doc_cleaner.py
```

## Non-goals

- Do not introduce new financial features.
- Do not change backend calculations/contracts.
- Do not start a third theme.
- Do not re-open the major page architecture already settled by packets 003-008 unless a concrete accessibility/responsive blocker requires it.
- Do not chase pixel-perfect sameness where component roles legitimately differ.

## Acceptance criteria

- [ ] Primary pages follow one coherent visual hierarchy.
- [ ] Secondary/admin pages no longer compete with primary finance workflows.
- [ ] Settings hides advanced command execution from normal preference flow.
- [ ] No scoped page has desktop-only fixed sidebar behavior at 360/768 widths.
- [ ] Keyboard order matches visual order.
- [ ] Focus states are visible in both themes.
- [ ] Heading hierarchy is valid and understandable.
- [ ] Loading/error/empty states are concise and action-oriented.
- [ ] Full frontend test/lint/build validation passes or exact pre-existing blockers are reported.

## Completion report

Report audited pages/breakpoints, accessibility fixes, residual known issues, removed dead UI, full validation results, and any deviation from the locked hierarchy.

---

## Progress report (2026-10-13) — code-level pass done; browser audit outstanding

Done:
- `TabbedPageLayout.vue`: row is `flex-col lg:flex-row`; sidebar gets `max-lg:w-full` so it stacks below content under 1024px (previously fixed `w-64`/`w-72 md:w-80` beside narrow content); tablist/tab/tabpanel semantics with `aria-selected`, roving `tabindex`, and Arrow/Home/End navigation that skips disabled tabs. New `TabbedPageLayout.spec.ts`.
- `Settings.vue`: order is Appearance → AI → Connected Accounts → collapsed "Advanced: local commands" `<details>` holding the command executor; test added.
- `FinancialSummaryDetailed.vue`: real `PageHeader` identity, date selector kept with the analysis. `Institutions.vue`: `PageHeader` with "Operator view" subtitle (replaces a bespoke centered accent h1); not promoted into nav.
- Heading audit: Dashboard keeps the single sr-only `h1`; the hero `h1` was already removed in TP-20261007-003. `PageHeader` provides the `h1` elsewhere.
- Validation: Vitest 50 files / 224 tests pass; lint 0 errors; build OK; `check_docs.py --changed-since origin/main` reports nothing to verify; `doc_cleaner.py` regenerated `docs/index/INDEX.md`.

Not done (why this packet stays open):
- No real-browser audit at 360/768/1024/1440, so overflow, clipped popovers, focus-visible in both themes, and tab order are unverified.
- Cypress targets for Dashboard/Accounts/Transactions/Planning were not run (need a dev server/backend; two Accounts component specs already fail locally for a missing router).
- Unified loading/empty/error state grammar and `RsaMonitor`/`FinancialSummaryDetailed` visual consistency were not swept; no dead-code removal beyond what 003-008 did.
- Resume condition: run the app, check each primary view at the four widths in both themes, fix findings, then complete.

---

## Progress report 2 (2026-10-13): breakpoint audit

**Done**
- Ran 10 routes (Dashboard, Accounts, Transactions, Forecast, Planning, Investments, Settings, Summary, Institutions, RSA Monitor) at 360/768/1024/1440 px in both themes (80 combinations) in Cypress's browser with `/api/**` stubbed empty. Measured page and element horizontal overflow and reviewed screenshots.
- Fixed root cause of missing page gutters and dead Tailwind spacing utilities: `main.css` re-imported `tailwindcss/preflight` and `tailwindcss/utilities` after `@import 'tailwindcss'`, which let the preflight reset (`padding: 0; margin: 0`) beat utilities such as `px-4`. Removed the duplicate imports.
- Fixed Forecast horizontal scroll at <1280 px (hidden tooltips widened the page; now anchored to the panel) and the 7-column adjustments form at narrow widths.
- Fixed Investments overview grid at <1024 px (2 columns) and <480 px (1 column).
- Result: no horizontal overflow in any of the 80 combinations.

**Not done (packet stays In Progress)**
- Manual focus-visible and tab-order check in both themes.
- Cypress e2e/component specs for primary views against a real backend.
- Unified loading/empty/error state grammar.
- Secondary-view sweep with seeded data (audit used empty responses) and dead-code removal.
- Noted, unfixed: Transactions search icon overlaps the placeholder text at 360 px.

---

## Completion report (2026-10-13)

Closed on owner acceptance after the code-level pass (771286a22) and the 80-combination breakpoint/theme audit (41394e97a): no horizontal overflow at 360/768/1024/1440 in either theme; page gutters and Tailwind spacing utilities restored; Forecast and Investments narrow-width fixes.

**Deferred (not completed, accepted by owner):**
- Manual focus-visible and tab-order check in both themes.
- Cypress specs for primary views against a real backend.
- Unified loading/empty/error state grammar.
- Seeded-data audit, secondary-view sweep and dead-code removal.
- Transactions search icon overlaps placeholder at 360 px.
