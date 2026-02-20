## LinkedAccountsSection.vue

Overview card that groups linked accounts by type and institution with optional rewards metadata.

### Props

- `accounts: Array` – Optional list of account objects `{ id, name, institution, type, subtype?, mask?, apr?, balance?, limit?, status?, promotions? }`.
- `useDemoFallback: Boolean` (default `false`) – Controls whether demo accounts are shown when `accounts` is empty.
- `enablePromotionEditor: Boolean` (default `false`) – Controls whether the inline add-promotion form is rendered.

### Data & Derived State

- `resolvedAccounts` sorts provided accounts by a preferred type order (`Credit Card`, `Deposit Account`, `Investment`) then name.
- If `accounts` is empty and `useDemoFallback` is `true`, `resolvedAccounts` uses the internal demo dataset.
- If `accounts` is empty and `useDemoFallback` is `false`, the section renders the empty real-data state.
- `groupedAccounts` maps accounts into `{ type, label, institutions: [{ name, accounts }] }`.
- `promotionEntries`/`promotionForms` track per-account reward rows and input state.

### UI & Interactions

- Renders type sections, then institution cards, then account rows.
- Each account shows balance/limit/status and a “Rewards & Promotions” details block.
- Promotion list entries are always rendered from incoming `promotions` and any local additions in current component state.
- Promotion editor behavior:
  - Hidden by default (`enablePromotionEditor=false`) for non-persistent integrations.
  - When shown, displays a local-state notice: “Local draft only. Promotions are not persisted yet.”
  - Allows category + optional custom category + rate input.

### Emits & Persistence

- Emits `add-promotion` with payload `{ accountId, category, rate }` after local validation and insertion.
- The component itself does not call APIs. Parent views are responsible for persistence, toasts, and rollback/error handling when connected to backend support.

### Integration Notes

- Accounts route usage should pass real mapped account data and explicitly set `:use-demo-fallback="false"`.
- Keep the editor hidden until backend persistence exists, or enable it and handle `@add-promotion` in the parent with success/error feedback.
- If account types change, update `typeSortOrder` and `accountTypeLabels` so grouping labels stay consistent.
