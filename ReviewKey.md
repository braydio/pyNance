# ReviewKey

This document consolidates **FileLegend.md** and **ProcessLegend.md** into a single master tracker. Use it to guide the Dashboard.vue UX/UI review and implementation.

## Legend
- **[D]** = `frontend/src/views/Dashboard.vue`
- **[AL]** = `frontend/src/components/layout/AppLayout.vue`
- **[TAS]** = `frontend/src/components/widgets/TopAccountSnapshot.vue`
- **[DNC]** = `frontend/src/components/charts/DailyNetChart.vue`
- **[CBC]** = `frontend/src/components/charts/CategoryBreakdownChart.vue`
- **[CWTB]** = `frontend/src/components/ui/ChartWidgetTopBar.vue`
- **[AS]** = `frontend/src/components/widgets/AccountSnapshot.vue`
- **[AT]** = `frontend/src/components/tables/AccountsTable.vue`
- **[TT]** = `frontend/src/components/tables/TransactionsTable.vue`
- **[PC]** = `frontend/src/components/tables/PaginationControls.vue`
- **[TM]** = `frontend/src/components/modals/TransactionModal.vue`
- **[GCD]** = `frontend/src/components/ui/GroupedCategoryDropdown.vue`
- **[UTIL]** = utilities/composables used for data or formatting
- **[README]** = `frontend/src/views/README.md`

---

## Phase 1: Audit & Documentation
### 1.1 Automated UI/UX Audit
- Use mobile emulation (Chrome DevTools or similar) at <600px, 768px, and >1024px to audit Dashboard layout.
- Document spacing, card layout, overflow, and responsive behavior of every direct child component.
- **Files:** [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD]

### 1.2 Code Audit
- List props and emitted events of all imported components.
- Identify magic numbers in Dashboard and child components.
- Inventory direct API calls, data-fetching logic, and refs.
- **Files:** [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD], [UTIL]

### 1.3 Create Baseline Documentation
- Add or update JSDoc comments for methods, computed props, and component props.
- Start or update README with a component map and UX flows.
- **Files:** [D], [README], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD]

---

## Phase 2: Layout, Spacing & Responsiveness
### 2.1 Responsive Layout Refactor
- Convert main container layout to CSS Grid if needed so cards align at all sizes.
- Standardize max/min width classes and review for consistency.
- **Files:** [D], [AL], [TAS], [DNC], [CBC], [AS]

### 2.2 Spacing/Styling Pass
- Replace hardcoded paddings and margins with theme utility classes.
- Apply consistent border radius, shadows, and backgrounds to cards and panels.
- **Files:** [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD]

### 2.3 Scroll & Sticky Elements
- Make table sections scrollable with sticky headers.
- Ensure modals fit within viewport with scroll if needed.
- **Files:** [D], [AT], [TT], [TM]

---

## Phase 3: Components, Slots, and Best Practices
### 3.1 Props Validation & Defaults
- Add `props` validation (type, required, default) to every child component.
- Document prop shapes where objects or arrays are passed.
- **Files:** [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD], [D]

### 3.2 Scoped Slots/Reusable Headers
- Refactor repeated control sections into a `<CardHeader>` component using named slots for title, actions, and extra controls.
- **Files:** [D], [CWTB] and potentially new `CardHeader.vue`

### 3.3 Extract Logic & UI
- Move API/data-fetching logic into composables such as `/composables/useDashboardData.js`.
- Split large table or modal markup (>150 lines) into subcomponents.
- **Files:** [D], [UTIL], [AT], [TT], [TM]

---

## Phase 4: Accessibility & Feedback
### 4.1 Accessibility Fixes
- Add or verify `aria-labels`, keyboard navigation, and semantic HTML for all actionable controls.
- Ensure proper heading levels and semantic tags for sections and tables.
- **Files:** [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD]

### 4.2 Color & Contrast Audit
- Run accessibility tools (Lighthouse, axe) to verify contrast and adjust variables.
- Replace fixed chart colors with a color-blind-safe palette where needed.
- **Files:** [D], [TAS], [DNC], [CBC], [AS], [AT], [TT], [TM]

### 4.3 Loading, Error, Empty States
- Add skeleton loaders or spinners for async sections.
- Include friendly empty states and error handling blocks for lists, tables, and charts.
- **Files:** [D], [AT], [TT], [TM], [CWTB]

---

## Phase 5: Enhanced Interactions
### 5.1 UI/UX Interactions
- Add animated transitions for expanding and collapsing tables or modals.
- Use clear iconography for toggles and provide tooltips for buttons and stats.
- **Files:** [D], [TT], [AT], [TM], [CWTB]

### 5.2 Chart/Data Improvements
- Allow users to select custom date ranges via a date picker.
- Add axis labels, legends, and captions to all charts.
- **Files:** [D], [TAS], [DNC], [CBC]

### 5.3 State Persistence
- Store expanded/collapsed UI states in localStorage or the user profile when available.
- **Files:** [D], [UTIL]

---

## Phase 6: Code Cleanup & Reliability
### 6.1 Refactor Logic
- Break up large methods into smaller composables or functions.
- Remove dead code, unused imports, and unused variables.
- Replace manual date manipulation with date-fns or dayjs.
- **Files:** [D], [UTIL], all API/data-handling components

### 6.2 Error Handling
- Standardize API error handling and logging.
- Provide fallback UI for network or data errors.
- **Files:** [D], [UTIL]

---

## Phase 7: Visual & Cosmetic Polish
### 7.1 Color & Typography Consistency
- Replace hardcoded colors with theme variables and limit font sizes.
- Ensure consistent font weight and font family across components.
- **Files:** All UI components and theme/CSS files

### 7.2 Iconography
- Audit icon usage, unify to one set, and add icons for all key actions.
- **Files:** [D], [TAS], [DNC], [CBC], [AS], [AT], [TT], [TM], [CWTB]

---

## Phase 8: Unpolished/Incomplete Features
### 8.1 Spending Insights Panel
- Add a placeholder card with spinner/progress and a clear "coming soon" label if incomplete.
- **Files:** [D]

### 8.2 Modal & Pagination Controls
- Ensure modals trap focus, close with Esc, and are accessible.
- Add loading or disabled states to pagination controls.
- **Files:** [TM], [PC]

---

## Phase 9: Testing
### 9.1 Unit/Snapshot Tests
- Add or expand test coverage for Dashboard.vue and new components/composables.
- Write tests for expanded/collapsed state, loading and error states, and data fetching.
- **Files:** All components with test files under `/frontend/tests/unit` and `/frontend/tests/components`

---

## Phase 10: Final Documentation & Review
### 10.1 Final Review
- Re-audit the dashboard for mobile, accessibility, and regression issues.
- Update the README with all UX, component, and data changes, listing breaking changes if any.
- **Files:** [D], [README]

---

## Steps-to-Files Summary

| Step     | Files to Change/Review                                             |
| -------- | ------------------------------------------------------------------ |
| 1.1, 1.2 | [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD], [UTIL] |
| 1.3      | All above + [README]                                               |
| 2.1      | [D], [AL], [TAS], [DNC], [CBC], [AS]                               |
| 2.2, 2.3 | All UI components                                                  |
| 3.1      | All components with props                                         |
| 3.2      | [D], [CWTB], potential new [CardHeader]                            |
| 3.3      | [D], [UTIL], [AT], [TT], [TM]                                      |
| 4.x      | All UI components, focus on [D], [AL], [TT], [AT], [TM]           |
| 5.x      | [D], [TT], [AT], [TM], [CWTB], [UTIL]                              |
| 6.x      | [D], [UTIL], all API/data components                               |
| 7.x      | All UI components, theme/CSS                                       |
| 8.x      | [D], [TM], [PC]                                                   |
| 9.x      | All, add/expand tests under `/tests/unit`                          |
| 10.x     | [D], [README]                                                      |

