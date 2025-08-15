# Frontend Component Architecture and Migration Guide [COMPONENTS_MIGRATION]

This document defines a scalable, semantically organized, and maintainable folder structure for Vue components within the pyNance frontend application, aligned with project conventions and actual directory contents.

**Purpose:** Establish clear component organization patterns and migration pathways for improved maintainability and developer experience.

---

## ✅ Goals

- Establish clear subdirectory groupings for components
- Prevent UI bloat by separating concerns (layout, data views, widgets)
- Align with Tailwind design system and existing `/docs/`
- Support future growth with logical nesting and reuse patterns
- Reduce decision-making overhead for devs

---

## 📁 Proposed Directory Structure (Revised)

```
frontend/src/components/
│
├── base/                 # UI primitives (card, table shell, etc.)
│   └── BaseCard.vue
│   └── BaseTable.vue
│   └── BaseInput.vue
│
├── layout/              # App shell wrappers
│   └── AppLayout.vue
│   └── Navbar.vue
│
├── charts/              # All chart-based components
│   └── Chart.vue
│   └── DailyNetChart.vue
│   └── CategoryBreakdownChart.vue
│   └── NetIncomeCharts.vue
│   └── NetYearComparisonChart.vue
│   └── AccountsReorderChart.vue
│   └── AssetsBarTrended.vue
│
├── tables/              # Structured row/column UI
│   └── AccountsTable.vue
│   └── AccountsTableLite.vue
│   └── TransactionsTable.vue
│   └── ManualTransactionTable.vue
│   └── UpdateTransactionsTable.vue
│
├── forms/               # Input controls, file selectors, modals
│   └── TransactionUploadCSV.vue
│   └── UploadCSV.vue
│   └── UploadDownloadCSV.vue
│   └── ImportFileSelector.vue
│   └── LinkAccount.vue
│   └── LinkProviderLauncher.vue
│   └── LinkAccountFullProducts.vue
│   └── MatchingTransactionUpload.vue
│   └── TokenUpload.vue
│   └── PlaidProductScopeSelector.vue
│
├── widgets/             # Dashboard widgets and UI enhancements
│   └── RefreshControls.vue
│   └── RefreshPlaidControls.vue
│   └── RefreshTellerControls.vue
│   └── YoutubeEmbed.vue
│   └── RecurringCalendar.vue
│   └── Settings.vue
│
├── layout/backups/      # Unused or legacy layout code (can be archived)
├── forecast/            # Forecast-specific subcomponents (TBD)
├── recurring/           # Recurring transaction UIs (TBD)
├── ui/                  # Visual-only UI enhancements (future devs)
```

---

## 🔁 Classification Process (Updated)

1. **Inventory** all components recursively
2. Use naming + content inspection to determine:

   - Is it a UI primitive (goes to `base/`)?
   - Does it render a chart (goes to `charts/`)?
   - Is it a table with rows/data bindings (goes to `tables/`)?
   - Is it file/CSV/input-related (goes to `forms/`)?
   - Is it layout, modal, or fixed shell (goes to `layout/`)?
   - Is it a utility or dashboard display (goes to `widgets/`)?

---

## 🛠️ Next Developer Actions

- Move physical `.vue` files into the new folders
- Update all related imports
- Add `README.md` with a short purpose description for each subfolder
- Clean up any duplicated or unused legacy components

---

## 📌 Notes

- `base/` should contain only stateless utility-style components
- `charts/` may later include `BaseChart.vue` if it becomes reusable
- `forecast/` and `recurring/` should be reviewed and reclassified after inspection
- `ui/` is a placeholder for future purely visual subcomponents (badges, tags, etc.)

---

This is the canonical structure for Vue component organization in `pyNance` moving forward. All new and migrated components must adhere to this layout.
