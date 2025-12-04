## PlaidProductScopeSelector.vue

Lightweight toggle grid for picking Plaid product scopes before launching Link. It is controlled via `v-model` (array of product ids) and emits `update:modelValue` on every toggle.

### Props

- `modelValue: string[]` – Selected Plaid product identifiers. Defaults to `[]`.

### Emits

- `update:modelValue` – Emits the next string array after a toggle.

### Behavior

- Available products: `transactions`, `investments`, `liabilities`.
- Click to toggle a product; active items render as filled (“pill”) buttons, inactive as outlined.
- No validation is enforced here; parent should block Link launch if the array is empty.

### Usage

```vue
<PlaidProductScopeSelector v-model="selectedProducts" />
<!-- Later -->
<LinkProviderLauncher :selected-products="selectedProducts" />
```

### Notes

- The selector is purely UI state; it does not persist. Persist or preselect in the parent if needed.
- If you add new Plaid products, update `availableProducts` in the component and any backend allowlists.\*\*\*
