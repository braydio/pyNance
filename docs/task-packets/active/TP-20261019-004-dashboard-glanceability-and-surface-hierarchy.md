# TP-20261019-004: Dashboard Glanceability, Panel Hierarchy and Overflow

**Packet ID:** TP-20261019-004  
**Status:** Ready  
**Created:** 2026-10-19  
**Last updated:** 2026-10-19  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261019-004-dashboard-glanceability-and-surface-hierarchy.md`  
**Priority:** P1  
**Workstream size:** One independently testable implementation packet  
**Depends on:** TP-20261019-003 (table chrome baseline)  
**Series:** Four packets (002 → 003 → 004 → 005), ordered due to shared summary/style contracts.

## Outcome
The Dashboard first viewport should communicate **what I can safely spend, what changed, and whether anything needs action** within seconds. Replace the dense three-box information dump with one visual/numeric lead and one concise supporting metric. Remove the repeated hairline, same-color-panel outlines throughout app shells and dashboard. **Professional does not mean thicker identical borders**: hierarchy comes from spacing, tonal surface variation, one strong focal point, and purposeful outlines.

## Confirmed seams on main 360fb21dc5a60d5d7cb93508a214584eba07f1de
- `frontend/src/components/dashboard/NetOverviewSection.vue`: tier 1 is `grid-cols-3` with **three bordered cards** (`surface-primary` SafeToSpend, `surface-normal` Transactions and Cash Direction); then another bordered `daily-net-chart-panel net-overview-panel surface-normal` and a `surface-quiet` Financial Summary wrapper. Text repeats selected-period and income/expense totals.
- `frontend/src/components/dashboard/SafeToSpendCard.vue`: eagerly renders lead amount + payload message + protected total + multiple window lines + warnings + 4-component financial breakdown + reserved summary & toggles. That is a useful audit trail, but a poor always-visible hero.
- `frontend/src/assets/css/main.css`: `.surface-primary`, `.surface-normal`, `.surface-quiet` ALL define 1px borders and similar rounded rectangles. `.dashboard-panel` adds yet another border/shadow and `NetOverviewSection.vue::.net-overview-panel` overrides border/shadow. `frontend/src/components/base/BasePanel.vue` defaults `borderTone=subtle`. These cumulative wrappers help create repeated outlined boxes.
- Chart below first tier already visualizes cashflow, so a second fully fledged net mini-chart would duplicate information. The Safe-to-Spend daypart and Cash Direction date window are **different horizons** and must not be presented as a single reconciled cash balance.

## Decisions and exact edits
1. **One compact “Now” composition**, in `NetOverviewSection.vue` (and `Dashboard.vue` data handoff if needed): lead **Safe to Spend amount** with short unit/horizon label and status. Secondary **Economic Net for selected chart period** with its exact range; compact third inline **N transactions in period** link/action or a single review indicator **only when it truly reflects actionable review**, not count=needs-attention. No three equal competing cards. Desktop: dominant 2/3 lead surface + compact 1/3 supporting rail; mobile: stack lead first, other stats one row or two tight lines. Keep date selector by chart, not repeated in “Now”.
2. **SafeToSpendCard progressive detail:** first viewport displays one amount + confidence/coverage state + short “protects through [date]” + at most one important caveat. Put formula components, projections, warning detail, reserved obligations and supporting messages under a single meaningful “How calculated / Upcoming obligations” disclosure (reuse existing reserve toggle semantics/test IDs). Critical shortfall/unreliable/no-data/error warnings must remain immediately visible with action; never hide them merely for visual cleanliness. Retain Today / Until Payday / Next 7 Days mode control with an unmistakable indication that amounts are **mode-specific**, and do not call daily allowance an unrestricted cash balance.
3. **One honest visual:** if server components are coherent (spendable cash, upcoming outflows, buffer, protected room) add a narrow neutral financial allocation/bridge strip with accessible exact numbers and correct sign, using source fields. Do **not** invent additive percentages or render stacked bars unless invariant `spendable - obligations - buffer = protected` (per actual backend contract) is true; otherwise a small horizon timeline/due-soon iconography is better than a false gauge. Alt text / semantic description must state what graphic measures; never imply economic net and Safe to Spend are the same basis.
4. **Surface hierarchy:** `frontend/src/assets/css/main.css` `surface-*`, `dashboard-panel`; `frontend/src/styles/theme.css` limited to semantic neutral surface/elevation tokens (do not change Nightfox palette); `frontend/src/components/base/BasePanel.vue`, `BaseCard.vue`, and `frontend/src/components/dashboard/NetOverviewSection.vue`:
   - Primary: exactly one prominent filled/elevated focal area per view; may have intentional thicker **accent rail** on genuinely important status; not every panel.
   - Normal: mild tone/elevation without full perimeter borders by default.
   - Quiet: transparent or subtle inset region, **no border by default**; separators only between sibling content.
   - Attention: semantic left rail + text/icon; accents reserved for status/action/selection, never gratuitous identical outlines.
   - No nested `card > panel > chart/table shell` double outlines, trim redundant shadows; deliberate shared radius/spacing. Provide opt-in `outlined` or `separator` variant for form controls/tables where boundary is required; preserve focus outline and contrast.
   - Audit `frontend/src/views/Accounts.vue`, `Transactions.vue`, `Investments.vue`, `Planning.vue`, `Forecast.vue` **at shell level only** for repetitive outline nesting/spacing (content/table details owned by 003/005). Do not regress existing `DailyNetChart.vue` TP-20261019-001 aggregation or axis.
5. **Overflow and geometry:** check `frontend/src/components/layout/AppLayout.vue`, `BasePageLayout.vue`, `TabbedPageLayout.vue`, `NetOverviewSection.vue`, `SafeToSpendCard.vue`, `FinancialSummary.vue`, chart expansion/toolbar popovers, sidebars, table shell parents. One intentional horizontal scroller for wide ledger; `min-width:0` for flex/grid children; no x-body scrolling at 360–390px; no popovers clipped by parent; no focus rings cut off; independent scroll/sticky regions cannot obscure table headers or chart labels. Status/reconnect controls stay accessible.
6. Update `docs/frontend/PRODUCT_UI_HIERARCHY.md` and `docs/frontend/THEMING_GUIDE.md` with actual surface roles and dashboard “Now” view rules, reconciling the earlier “one dominant surface” guidance with new borderless quiet panels.

## Acceptance and visual QA
- At 390/768/1280/1920px: primary action/number unmistakable; user can identify two key metrics and their **different horizons** without reading an essay; all detailed Safe-to-Spend computations still available on demand; no more three equally styled cards in first tier.
- 6 sibling regions do NOT all show indistinguishable 1px outlines; compare screenshot side by side before/after. At least 3 distinct treatments are demonstrated: raised focal, neutral open region, attention rail. Check typography, number alignment, theme contrast, mouse/keyboard and panel flow.
- Loading/errors/unknown owner/negative or zero allowance, no upcoming bills, confidence-warning and reconnect states retain critical context and truthful CTA. Mode switching does not leak stale figures or change selected Cash Flow interval.
- Run `cd frontend && npm run test -- --run src/components/dashboard/__tests__/SafeToSpendCard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts src/views/__tests__/Dashboard.spec.ts src/components/layout/__tests__/BasePageLayout.spec.ts src/components/layout/__tests__/TabbedPageLayout.spec.ts && npm run build`; run `frontend/cypress/e2e/dashboard.cy.js` and `frontend/cypress/e2e/ui-visual-regression.cy.js` if available, document actual screenshots/failures. Existing Dashboard baseline test failures must be compared with base main.
- No invented finance metric, no CSS “fix” that hides content under `overflow:hidden`, no changed bank semantics/forecast math or chart bucketing. **Owner:** dashboard top-tiers, shell/surface CSS/token/primitives; avoid rewriting 003's table cells and 005's domain rows.


## Execution and closeout
Follow `AGENTS.md` and `docs/task-packets/README.md`: pause `scripts/dev-watcher.sh` only if running, preserve unrelated dirty files; inspect only named seams, mark packet/TRACKER In Progress, implement focused scope and tests, then mark Complete/move to completed and update INDEX/TRACKER in the same committed change. Sync/push `origin/main` without force, resume watcher if paused. Provide exact `Workstream`, status, commit link, changed files, totals/visual acceptance evidence, executed commands/results, unrun checks and blockers. Do not mark a failing or unverified test as passed.
