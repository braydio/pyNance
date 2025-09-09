# Accounts Page: Granular Institution & Account Info

## Overview

The **Accounts Page** provides a detailed, organized view of all user accounts grouped by financial institution. It surfaces granular information, trends, and actions for both institutions and individual accounts.

---

## Layout & Features

### 1. Institution Overview

- **Institution Filter/Dropdown**  
  - Select "All" or filter by specific institution (bank, credit union, etc.)

- **Institution Cards**
  - Logo & Name
  - Total balance (sum of all accounts at this institution)
  - Number of accounts
  - Last synced date
  - Connection status (connected, needs update, error)

---

### 2. Accounts List

- **Accounts Table or Cards (per institution):**
  - Account Name / Type (e.g., Checking, Savings, Credit Card, Loan)
  - Institution Name (with logo)
  - Last 4 digits
  - Current Balance (positive/negative style)
  - Account Status (active, hidden, closed)
  - Labels/Tags (e.g., “Joint”, “Investment”)
  - Action Menu: Rename, Hide, Sync, View Details

- **Per Account:**
  - Mini trend chart (30-day/6-month balance)
  - This month's spending/income summary

---

### 3. Account Detail View (Drawer/Modal)

When a user clicks "View Details" on any account:

- Full transaction list (filter/search)
- Monthly summaries: Deposits, Withdrawals, Fees
- Category breakdown (Pie/Bar Chart) for spending by this account
- Account info: Routing/account numbers (masked), account type, open date
- Option to add manual transaction (if supported)
- Download/Export button (CSV/PDF)

---

### 4. Institution-level Insights

- Total balances, liabilities, assets for institution
- Top spending categories (across institution)
- Recent transactions (across all institution accounts)
- Institution-specific alerts (e.g., "Low balance", "Overdraft detected")

---

### 5. Quick Actions

- Add new account
- Sync institution
- Hide/Show closed accounts
- Download CSV/PDF report
- Link new institution
### 6. Account Groups

- Create custom account groups to organize frequently used accounts.
- Groups persist in `localStorage`; the last active group is restored on page
  reload.
- Reorder accounts within a group by dragging the handle next to each entry.
- Double-click a group tab to edit its name and press <kbd>Enter</kbd> to save.
- Each group can include up to **five** accounts; create another group or
  remove one to add more.

---

## UX Patterns

- **Sidebar:** List of institutions for quick filter
- **Tabs:** All Accounts | By Institution | Hidden | Closed
- **Search bar:** Filter accounts by name, type, number
- **Mobile:** Collapsible cards, swipe for hide/sync

---

## Example Visual Layout

```text
| Bank of America (3 accounts)   [Sync]  [Total: $12,320.50]
|   - Main Checking  ...$8,210.25    [chart] [View]
|   - Travel Credit  ...$-900.12     [chart] [View]
|   - Old Savings    ...$5,010.37    [chart] [View]
|
| Chase (2 accounts)              [Sync]  [Total: $2,430.70]
|   - Sapphire Checking ...$2,100.45 [chart] [View]
|   - Slate Credit     ...$330.25   [chart] [View]
|
| [Add Account] [Download CSV]
```
