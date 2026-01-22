## PlaidProductScopeSelector.vue

Card-style selector for picking Plaid product scopes before launching Link. It is controlled via `v-model` (array of product ids) and emits `update:modelValue` on every toggle.

### Props

- `modelValue: string[]` – Selected Plaid product identifiers. Defaults to `[]`.

### Emits

- `update:modelValue` – Emits the next string array after a toggle.

### Behavior

- Available products: `transactions`, `investments`, `liabilities`.
- The selector renders a "Choose data to share" label with card-like buttons that include inline helper text for each product.
- Click to toggle a product; active cards render with a highlighted border and shadow, inactive cards retain the default border.
- No validation is enforced here; parent should block Link launch if the array is empty.

### Usage

```vue
<PlaidProductScopeSelector v-model="selectedProducts" />
<!-- Later -->
<LinkProviderLauncher :selected-products="selectedProducts" />
```

### Notes

- The selector is purely UI state; it does not persist. Persist or preselect in the parent if needed.
- If you add new Plaid products, update `availableProducts` in the component and any backend allowlists.
