# PageHeader Component

Standard page header used at the top of views. Provides slots for an optional icon, title, subtitle, and an `actions` area on the right.

## Slots
- `icon` – optional leading icon
- `title` – main heading text
- `subtitle` – supporting description text
- `actions` – optional right‑aligned controls (e.g. buttons)

## Example
```vue
<PageHeader>
  <template #icon>
    <CreditCard class="w-6 h-6" />
  </template>
  <template #title>Transactions</template>
  <template #subtitle>View and manage your transactions</template>
  <template #actions>
    <UiButton variant="outline">Import</UiButton>
  </template>
</PageHeader>
```
