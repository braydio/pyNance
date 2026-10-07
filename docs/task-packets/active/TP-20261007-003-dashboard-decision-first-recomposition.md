# TP-20261007-003: Dashboard Decision-First Recomposition

**Packet ID:** TP-20261007-003  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-003-dashboard-decision-first-recomposition.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-001, TP-20261007-002  
**Priority:** High  
**Series:** UI/UX reauthor, packet 2 of 8  

## Objective

Turn Dashboard from a collection of equally prominent widgets into a financial command center. The first screenful must prioritize the user's current spend guardrail, items requiring action, and current cash direction. Exploratory breakdowns and deep account/transaction surfaces move later or become explicit navigation.

## Confirmed current-state problems

Files:

- `frontend/src/views/Dashboard.vue`
- `frontend/src/components/dashboard/NetOverviewSection.vue`
- `frontend/src/components/dashboard/SafeToSpendCard.vue`
- `frontend/src/components/dashboard/CategoryBreakdownSection.vue`
- `frontend/src/components/SpendingInsights.vue`

Current hierarchy issues:

1. `NetOverviewSection` begins with a very large 4xl/5xl "Welcome" hero, date, LLM message, and review pill. It consumes primary visual space without answering the most important financial question.
2. Review state appears in the hero and again as a full standalone "Review Transactions" CTA card.
3. Date-range controls appear before the main decision surfaces even though they primarily control analysis.
4. Dashboard later contains a `min-h-[55vh]` to `65vh` "Choose a lower dashboard surface" panel that embeds Accounts/Transactions content. This duplicates dedicated routes and substantially increases page length/mental context.
5. Category breakdown adds three story cards, chart controls, ranking rows, total, and a separate SpendingInsights module, causing secondary analysis to compete with primary decisions.
6. Accent borders, angular dividers, gradients, status pills, and multiple card treatments are all active at once.

## Target information hierarchy

### Tier 1: Now

Top of page, visible without scrolling on normal desktop:

- **Safe to Spend** as the dominant decision metric.
- **Needs attention** compact action queue, beginning with transaction review count and any available connection/reconnect condition already exposed to the frontend.
- **Current cash direction** concise net/income/expense status for the selected default period.

### Tier 2: Trend

- Daily Net chart.
- Date range/timeframe and chart overlays live with the chart, not above the entire page.
- FinancialSummary becomes a compact supporting interpretation of the trend, not another hero.

### Tier 3: Explain

- Spending by category/merchant.
- SpendingInsights.
- Top account snapshot.

### Tier 4: Drill down

- Compact links/actions to dedicated Accounts and Transactions routes.
- Do not embed full account/transaction workbenches on Dashboard.

## Required changes

### 1. Replace the oversized greeting hero

File:

- `frontend/src/components/dashboard/NetOverviewSection.vue`

Replace the 4xl/5xl welcome block with a compact dashboard header/context strip.

Keep:

- user/date context when useful;
- `netWorthMessage` as a single subdued contextual line;
- accessibility heading.

Do not let greeting copy become the largest text on the page.

### 2. Make Safe to Spend the primary decision surface

Files:

- `frontend/src/components/dashboard/SafeToSpendCard.vue`
- `frontend/src/components/dashboard/NetOverviewSection.vue`

Requirements:

- amount is the visual anchor;
- status and horizon remain immediately legible;
- component breakdown is secondary and can be visually compact;
- loading/error states preserve the same footprint;
- avoid displaying "Confidence: unknown" as high-value chrome. If confidence is unavailable, omit/de-emphasize it rather than foreground uncertainty text;
- keep Today / Until Payday / This Week control.

### 3. Consolidate action-required state

File:

- `frontend/src/views/Dashboard.vue`

Remove the duplicate standalone Review Workflow card. Create one compact attention/action module in the Tier 1 area using the existing `reviewCount`, loading, error, tag-filter flow, and `openReviewModal`.

The default presentation should answer:

- how many transactions need review;
- primary action: Review;
- optional tag filtering only after the user chooses to refine, not as a permanently prominent form field.

Do not remove TransactionReviewModal behavior.

### 4. Move analysis controls to their analysis

File:

- `frontend/src/components/dashboard/NetOverviewSection.vue`

DateRangeSelector and Daily Net detail/timeframe controls must visually belong to the Daily Net analysis panel. Do not place a page-global date selector between the header and decision cards.

### 5. Remove embedded lower workbenches

File:

- `frontend/src/views/Dashboard.vue`

Remove/retire the large `tables-panel` expand/collapse flow for `AccountsSection` and `TransactionsSection` from Dashboard.

Replace it with a compact "Explore details" row using router links to:

- `/accounts`
- `/transactions`

Preserve chart-click transaction modals. The removal applies only to embedded full workbench expansion.

### 6. Quiet secondary analysis

File:

- `frontend/src/components/dashboard/CategoryBreakdownSection.vue`

Keep the category/merchant chart and top ranking, but reduce pre-chart story-card noise:

- do not render three equal story cards by default;
- present at most one concise lead insight plus the ranking/chart;
- controls become compact and aligned to the section header;
- ranking remains scannable;
- total remains visible.

`SpendingInsights` should read as complementary explanation, not equal hero content.

### 7. Responsive ordering

At narrow widths order content:

1. Safe to Spend
2. Needs attention
3. compact current cash status
4. Daily Net
5. category/spending explanation
6. detail links

No horizontal control overflow.

## Tests

Update:

- `frontend/src/views/__tests__/Dashboard.spec.ts`
- `frontend/src/components/dashboard/__tests__/DashboardSections.spec.ts`
- `frontend/cypress/e2e/dashboard.cy.js` where current selectors cover removed/reordered UI.

Must cover:

- one review CTA/action source, not duplicated;
- Safe to Spend appears before analytics;
- chart-click modals still work;
- account/transaction detail links route correctly;
- lower embedded workbench CTA/expansion is gone;
- Safe-to-Spend error remains visible.

## Non-goals

- Do not change Safe-to-Spend math/API.
- Do not change Daily Net calculation.
- Do not redesign transaction review internals.
- Do not add new backend endpoints.
- Do not remove category/merchant drill-down modals.

## Acceptance criteria

- [ ] First screenful prioritizes Safe to Spend + action-required state.
- [ ] Giant welcome hero is removed/reduced.
- [ ] Review Transactions is not duplicated.
- [ ] Date controls live with Daily Net analysis.
- [ ] Embedded Accounts/Transactions workbenches are removed from Dashboard.
- [ ] Dedicated Accounts/Transactions links replace the large drill-down shell.
- [ ] Category analysis is materially quieter.
- [ ] Chart transaction drill-down remains functional.
- [ ] Mobile content order preserves decision priority.
- [ ] Focused Dashboard tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/views/__tests__/Dashboard.spec.ts src/components/dashboard/__tests__/DashboardSections.spec.ts
npm run lint
npm run build
```

## Completion report

Report before/after hierarchy, removed duplicate surfaces, resulting component order, preserved interactions, responsive behavior, tests, and deviations.
