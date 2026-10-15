# pyNance UI Field Audit · 2026-10-14

**Method:** Static source audit of all 14 routes in frontend/src/router/index.js at commit 4dd3ac525643d5b519d40ee5420f52aacd9c9afa. No browser automation, rendered screenshots, user-account data, or actual pixel-overflow measurement was performed. Existing unregistered Mock/DashboardMock/TempDashboard views are excluded from production route scope.
**Implementation packets:** TP-20261014-010 to TP-20261014-022. Accounts feature packets 005-009 are separate prerequisites to 017.

## User-facing route and field inventory

| Route | View | Interactive field and hidden-state families |
| --- | --- | --- |
| / | Dashboard | hero/status, period/date, chart overlays, optional tag, financial details, category/merchant switch, group dropdown, account snapshot expand/edit, transaction/review modals |
| /accounts | Accounts | account select, refresh, reconnect, Overview/Activity/Trends/Connections, history, account groups, linked account disclosures, Plaid link modal |
| /transactions | Transactions | search, Filters/Import toggles, dates, account/type, chips, sort/edit grid and pagination, CSV, recurring and transfers |
| /forecast | Forecast | account scope, scenario presets, aspect/graph/window/model controls, assumptions/advanced disclosures, source modal |
| /planning | Planning | bill name/amount/due/frequency/category, validation, add/edit, bill list details/delete, allocation amounts |
| /investments | Investments | section menu, institution/account selects, expandable holdings, performance, six transaction filters/pagination, refresh/link |
| /settings | Settings | theme buttons, AI toggle/endpoint, Save, Plaid refresh, Advanced commands disclosure, template/argument/output |
| /institutions | Institutions | institution expand row/refresh and nested accounts table |
| /rsa-monitor | RSA monitor | Refresh, status cards, component grid, orders table, broker list, log scroll |
| /accounts/table | Account table | search, show/hide/delete/type filters, removable chips, account table, delete modal |
| /summary | Financial summary | date and zoom, chart, details expandable and selected-day drill-in |
| /charts/cashflow | Cashflow direct route | direct DailyNetChart requiring dates; wrapper needed |
| /charts/category | Category direct route | direct CategoryBreakdownChart requiring dates; wrapper needed |
| /charts/assets/year-comparison | Year comparison direct route | Assets/Liabilities/Net Worth toggles, chart loading/empty |

## Confirmed source findings

- frontend/src/styles/theme.css: dark text-muted #71839b over page #192330 contrast 4.09:1; Everforest muted #829181 over light surface #fdf6e3 contrast 3.08:1; over page #f3ead3 2.77:1; Everforest red #f85552 over light surface 3.04:1; green #8da101 2.69:1. These fall below 4.5:1 normal text AA. Computations are for specified solid colors, not translucent mixed surfaces.
- frontend/src/assets/css/main.css .input px-2 py-1 diverges from @utility ui-control-input px-3 py-1.5; BaseInput/BaseSelect and native fields create mismatched control heights.
- frontend/src/components/ui/Modal.vue lacks role=dialog, keyboard Escape and managed focus; close text-gray-500 hover:text-black and w-auto mt-20 geometry.
- frontend/src/components/ui/GroupedCategoryDropdown.vue is clickable div without Enter/Space; popup absolute with no max-height. frontend/src/components/dashboard/CategoryBreakdownSection.vue root overflow-hidden can clip popup (render verification required).
- frontend/src/components/ui/FuzzyDropdown.vue uses 180ms blur-close timeout; TogglePanel.vue uses .dark hardcoded grays rather than data-theme and white fallback.
- frontend/src/components/layout/Navbar.vue hides small-screen horizontal nav scrollbar without scroll cue.
- frontend/src/components/tables/UpdateTransactionsTable.vue uses 10 fixed columns and th click sorting, ellipsis on all cells, nested table min-h-[50vh] scroll.
- frontend/src/components/forecast/ForecastLayout.vue root bg-gray-50 and text-gray-500/red-600 bypass theme identity.
- frontend/src/views/Investments.vue hardcoded #6b7280 captions/status and six-column expandable holdings.
- frontend/src/components/tables/InstitutionTable.vue uses clickable tr without expand button/aria, nested table; frontend/src/components/ui/AccountSelector.vue clickable div selection cards.
- frontend/src/views/FinancialSummaryDetailed.vue initializes empty dateRange; direct /charts/cashflow and /charts/category mount charts without required date props.
- Planning, Settings, RSA monitor, Accounts maintenance and Investments each have additional per-field density/overflow/label edge cases requiring browser verification.

## Design language

Use semantic contrast tokens for Nightfox and Everforest rather than hardcoded utility grays; body >=1rem where practical, fields/labels >=0.875rem, meaningful dense secondary text >=0.8125rem with AA contrast. Surface hierarchy title > context > primary decision > analysis > advanced/maintenance, at most two nested card backgrounds in typical flows. Default section spacing 24/32px, card inset 16/20/24px, field group gap 8/12/16px. Shared input/select/button heights ~40px with named compact exceptions. Popovers and dialogs keyboard operable, aria state truthful, focus return, bounded scroll, no ancestor clipping; mobile safe at 320 and 390. Real HTML tables sort via buttons/aria-sort and local scroll; numeric columns tabular. Avoid broad z-index, width or padding overrides that mask structural issues.

## Packet ownership

- TP-20261014-010 Theme Contrast and Typography: frontend/src/styles/theme.css, frontend/src/assets/css/main.css, frontend/src/assets/css/theme.css, frontend/src/styles/typography.css
- TP-20261014-011 Shared Fields, Buttons, Date and Select Geometry: frontend/src/assets/css/main.css, frontend/src/components/base/BaseInput.vue, frontend/src/components/base/BaseSelect.vue, frontend/src/components/base/BaseButton.vue, frontend/src/components/ui/Button.vue, frontend/src/components/DateRangeSelector.vue
- TP-20261014-012 Dropdowns, Popovers and Expandable State: frontend/src/components/ui/GroupedCategoryDropdown.vue, frontend/src/components/ui/FuzzyDropdown.vue, frontend/src/components/ui/TogglePanel.vue, frontend/src/components/charts/ChartDetailsSidebar.vue, frontend/src/components/dashboard/CategoryBreakdownSection.vue, frontend/src/components/widgets/TopAccountSnapshot.vue
- TP-20261014-013 Modal Overlay Focus, Stacking and Scroll: frontend/src/components/ui/Modal.vue, frontend/src/components/forms/LinkAccount.vue, frontend/src/components/transactions/TransactionReviewModal.vue, frontend/src/components/modals/TransactionModal.vue, frontend/src/components/forecast/ForecastLayout.vue, frontend/src/components/tables/AccountsTable.vue
- TP-20261014-014 Navbar, Responsive Tabs and Shared Spacing: frontend/src/components/layout/Navbar.vue, frontend/src/components/layout/AppLayout.vue, frontend/src/components/layout/BasePageLayout.vue, frontend/src/components/layout/TabbedPageLayout.vue, frontend/src/components/ui/PageHeader.vue, frontend/src/components/ui/ChartWidgetTopBar.vue, frontend/src/views/Institutions.vue
- TP-20261014-015 Dashboard and Direct Chart Route Detail Polish: frontend/src/views/Dashboard.vue, frontend/src/views/FinancialSummaryDetailed.vue, frontend/src/router/index.js, frontend/src/components/dashboard/NetOverviewSection.vue, frontend/src/components/dashboard/CategoryBreakdownSection.vue, frontend/src/components/statistics/FinancialSummary.vue, frontend/src/components/statistics/DailySpendingPanel.vue, frontend/src/components/widgets/TopAccountSnapshot.vue, frontend/src/components/charts/DailyNetChart.vue, frontend/src/components/charts/CategoryBreakdownChart.vue, frontend/src/components/charts/NetYearComparisonChart.vue
- TP-20261014-016 Transactions Data Grid, Filters and Import: frontend/src/views/Transactions.vue, frontend/src/components/tables/UpdateTransactionsTable.vue, frontend/src/components/AccountFilter.vue, frontend/src/components/TypeSelector.vue, frontend/src/components/forms/ImportFileSelector.vue, frontend/src/components/recurring/RecurringTransactionSection.vue, frontend/src/components/transactions/InternalTransferScanner.vue
- TP-20261014-017 Accounts, Institutions and Account Selection UX: frontend/src/views/Accounts.vue, frontend/src/components/accounts/LinkedAccountsSection.vue, frontend/src/components/tables/AccountsTable.vue, frontend/src/components/tables/InstitutionTable.vue, frontend/src/components/ui/AccountSelector.vue, frontend/src/components/widgets/TopAccountSnapshot.vue, frontend/src/views/Institutions.vue
- TP-20261014-018 Forecast Scenarios and Assumptions UI Density: frontend/src/views/Forecast.vue, frontend/src/components/forecast/ForecastLayout.vue, frontend/src/components/forecast/ForecastSummaryPanel.vue, frontend/src/components/forecast/ForecastChart.vue, frontend/src/components/forecast/ForecastScenarioComparison.vue, frontend/src/components/forecast/ForecastAdjustmentsForm.vue, frontend/src/components/forecast/ForecastBreakdown.vue
- TP-20261014-019 Planning Bill Entry, List and Allocation Controls: frontend/src/views/Planning.vue, frontend/src/components/planning/PlanningSummary.vue, frontend/src/components/planning/BillForm.vue, frontend/src/components/planning/BillList.vue, frontend/src/components/planning/Allocator.vue
- TP-20261014-020 Investments Filter, Holdings and Expandable Rows: frontend/src/views/Investments.vue, frontend/src/components/charts/PortfolioAllocationChart.vue, frontend/src/components/forms/LinkProviderLauncher.vue
- TP-20261014-021 Settings, RSA Monitor and Utility Page Polishing: frontend/src/views/Settings.vue, frontend/src/views/RsaMonitor.vue, frontend/src/views/Institutions.vue, frontend/src/router/index.js, frontend/src/components/widgets/RefreshPlaidControls.vue
- TP-20261014-022 Every Route Visual and Keyboard QA Gate: frontend/src/router/index.js, frontend/cypress/e2e/ui-visual-regression.cy.js, docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Required browser verification still pending

For **every route**: Nightfox and Everforest at 320x568, 390x844, 768x1024, 1280x800, 1440x900 plus 200% text/zoom; default, open dropdown, expanded, modal, long-content, error, empty and loading states where supported. Record FAIL/PASS/BLOCKED per route and control in this document after task 022. Confirm actual scrollWidth, bounding boxes, computed contrast, dropdown visibility and keyboard focus. Do not label potential CSS collisions as browser-proven defects before capture.
