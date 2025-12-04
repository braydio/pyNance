## LinkedAccountsSection.vue

Overview card that groups linked accounts by type and institution with optional rewards metadata. Defaults to a demo dataset if no accounts are provided.

### Props
- `accounts: Array` – Optional list of account objects `{ id, name, institution, type, subtype?, mask?, apr?, balance?, limit?, status?, promotions? }`.

### Data & Derived State
- `resolvedAccounts` sorts provided accounts by a preferred type order (`Credit Card`, `Deposit Account`, `Investment`) then name; falls back to defaults.
- `groupedAccounts` maps accounts into `{ type, label, institutions: [{ name, accounts }] }`.
- `promotionEntries`/`promotionForms` track per-account reward rows and input state.

### UI & Interactions
- Renders type sections → institution cards → account rows.
- Each account shows balance/limit/status, then an always-open “Rewards & Promotions” details block:
  - Existing promotions listed from `promotions` prop or added entries.
  - Inline form to add a promotion (category picker with optional custom, rate input). Submits to local state only; no API call.

### Helpers
- `formatApr`, `formatBalance`, `formatPercentage` provide display-friendly strings.
- `addPromotion(accountId)` pushes a validated reward entry; rejects empty category or negative/NaN rates.

### Integration Notes
- To persist promotions, listen for a new emit (not currently emitted) or extend the component with an `@submit` hook to call your API.
- Provide real `accounts` data to avoid the demo dataset; ensure each account has a unique `id`.
- If you change account types, update `typeSortOrder` and `accountTypeLabels` so grouping labels stay consistent.***
