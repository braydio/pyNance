# PageHeader Component

Standard page header used at the top of views. Centers title and subtitle with an optional icon and `actions` area aligned to the right.

## Props
- `icon` – optional icon component rendered on the right

## Slots
- `title` – main heading text
- `subtitle` – supporting description text
- `actions` – optional right‑aligned controls (e.g. buttons)

## Example
```vue
<PageHeader :icon="CreditCard">
  <template #title>Transactions</template>
  <template #subtitle>View and manage your transactions</template>
  <template #actions>
    <UiButton variant="outline">Import</UiButton>
  </template>
</PageHeader>
```
