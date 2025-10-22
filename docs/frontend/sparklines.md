# Account Sparklines

This document covers the AccountSparkline component used within the TopAccountSnapshot widget to visualize recent account activity compactly.

- Location: `frontend/src/components/widgets/AccountSparkline.vue`
- Consumers: `frontend/src/components/widgets/TopAccountSnapshot.vue`

## Behavior
- Renders a lightweight SVG sparkline sized for list rows.
- Click/tap toggles between two data modes:
  - `balance` (recent balance history)
  - `transactions` (recent net amounts or transaction counts)
- An indicator dot displays the current mode: cyan for balance, yellow for transactions.

## Data Sources
- Balance history from `useAccountHistory(accountId, range)` with default `range = '30d'`.
- Transaction history from `useAccountTransactionHistory(accountId)`.
- If transaction history isn’t available, the component gracefully falls back to balance data to avoid blanks.

## Accessibility
- Provides `role="img"` and dynamic `aria-label` reflecting the current mode and account.
- Keyboard interaction is indirect (row is already keyboard-focusable in TopAccountSnapshot); the sparkline supports mouse/touch toggling.

## Integration Notes (TopAccountSnapshot)
- The sparkline is rendered in each account row using `:account-id="accountId(account)"`.
- Recent transactions list (expanded row) is fetched separately via `fetchRecentTransactions(accountId, limit)`, keeping sparkline fetches independent and fast.
- The parent list remains responsive; sparklines do not block interactions.

## Performance Tips
- Keep ranges short (e.g., 30 days) for snappy rendering.
- Avoid rendering sparklines off-screen; they’re lightweight but still benefit from list virtualization if needed.
- The component derives its own SVG `points` from the provided data; no external chart library is required.

## Styling
- Uses theme CSS variables for colors: `--color-accent-cyan` (balance) and `--color-accent-yellow` (transactions).
- Container is sized to `60x20` by default; adjust via parent styles if needed.

## API & Props
- `accountId` (string, required): The account identifier to fetch data for.

## Example
```
<AccountSparkline :account-id="account.account_id" />
```
