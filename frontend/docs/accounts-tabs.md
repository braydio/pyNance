# Accounts View Tab Layout

The Accounts view keeps `TabbedPageLayout` and uses four user-facing tabs:

1. `Overview`
2. `Activity`
3. `Analysis`
4. `Manage`

## Behavior Notes

- The `Plan Account` action is shown in **Overview** and **Manage** contexts.
- Planning navigation always includes both `accountId` and `selectedAccount` query values.
- `AccountActionsSidebar` is conditional and only renders for **Overview** and **Manage** to reduce visual noise.
- `Activity` contains the transactions workspace and owns its refresh interaction (`Refresh Activity`).
- `Analysis` centralizes shared filtering controls (range + account selector) above charts.
