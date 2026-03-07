## PlaidProductScopeSelector.vue

Card-style selector for picking Plaid product scopes before launching Link. It is controlled via `v-model` (array of product ids) and emits `update:modelValue` on every toggle.

### Props

- `modelValue: string[]` – Selected Plaid product identifiers. Defaults to `[]`.

### Emits

- `update:modelValue` – Emits the next string array after a toggle.

### Behavior

- Available products: `transactions`, `investments`, `liabilities`.
- The selector renders a "Choose what data to share" legend and matching group aria-label with segmented cards that explain what each scope enables in the app.
- Click to toggle a product; active cards render with a highlighted border and shadow, inactive cards retain the default border.
- No validation is enforced here; parent components provide empty-state messaging and block Link launch if the array is empty.

### Usage

```vue
<PlaidProductScopeSelector v-model="selectedProducts" />
<!-- Later -->
<LinkProviderLauncher :selected-products="selectedProducts" />
```

### Notes

- The selector is purely UI state; it does not persist. LinkAccount now starts with no preselected products and requires an explicit user selection before linking.
- If you add new Plaid products, update `availableProducts` in the component and any backend allowlists.
