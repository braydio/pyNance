# pyNance Frontend - Site Map & Issue Tracker (`frontend/src/views/`)

---

## Dashboard.vue

### Components & Tasks

#### Title & Greeting

- Update styling to match design standards.
- Theme username with distinct color.
- Use varying font sizes for multi-line layout.
- Third-line message should change based on total net worth:

  - Below \$0 → Display concerned, humorous, or sarcastic message.
  - Above \$1,000 → Display encouraging or smug commentary.
  - Message tone: amusing, insulting, sarcastic.

#### Account Snapshot

- Style section title to emphasize module distinction.
- Match 'Configure' button with UI theme.
- Submenu ("Select up to 5 accounts") should be a styled dropdown.
- Enable fuzzy find functionality in dropdown.
- Fix current display issue (module is not rendering).
- Show relevant snapshot info: account name, type, balance, etc.

#### Daily Net Income Chart

- Currently broken—no data displayed.
- Increase font size of axis labels.
- Remove legend (green/red is self-explanatory).

#### Spending by Category Chart _(Requested)_

- Currently not displaying any data.
- Axis labels too small—increase for readability.
- Style the chart title appropriately.
- Legend and category selectors are too large:

  - Move to a collapsible tab.
  - Add fuzzy search for categories.

- Fix layout overlap with transactions table using TailwindCSS.

#### Transactions Table

- Does not currently display data—requires fixing.
- Style amounts:

  - Expenses → Red font, parentheses (e.g. (\$1,250.00)).
  - Incomes → Green font.

#### Accounts Table

- Style balances using accounting format:

  - Dollar sign, 2 decimals, parentheses for negatives, red for negative or liability values.

- Normalize capitalization for 'Account Type' and 'Account Name'.
- Adjust spacing to ensure single-line entries.
- Consider adding Plaid Institution Icons per entry.
- Add pagination and/or scrolling.

### Global Dashboard TODOs

- Fix non-functional components.
- Refactor for consistent UI/UX.
- Audit data display logic per component.

---

## Accounts.vue

### Components & Tasks

#### Header Greeting

- Adjust font sizing for visual hierarchy.
- Apply themed colors to font.

#### Link Account Section

- Make menu an expandable/collapsible dropdown.
- Style "Refresh Plaid/Teller" subtitles.
- Style and theme: date pickers, account selectors, refresh buttons.
- Improve section layout and aesthetic.
- Implement Teller-specific product selection.
- Add 'Link Account' button:

  - Place near Product selection.
  - Only enabled when a product is selected.

- Make entire section expandable/collapsible.

#### Assets Year Comparison Chart

- Component is non-functional—fix rendering.

#### Net Assets Trend Chart

- Component is non-functional—fix rendering.

#### Issues / TODOs

- ***

## Transactions.vue

### Components

-

#### Issues / TODOs

- ***

## Investments.vue

### Components

-

#### Issues / TODOs

- ***

## Forecast.vue

### Components

-

#### Issues / TODOs

- ***

## ForecastMock.vue

### Components

-

#### Issues / TODOs

- ***

## DashboardMock.vue

### Components

- `DashboardMockLayout.md`
- `DashboardMockTransactions.vue`
- `TopBar.vue`

#### Issues / TODOs

- ***

## RecurringTX.vue

### Components

-

#### Issues / TODOs

- ***

## RecurringScanDemo.vue

### Components

-

#### Issues / TODOs

- ***

## Settings.vue

### Components

-

#### Issues / TODOs

- ***

## Mock Components Directory (`/Mock/`)

### Components

- AccountToggle.vue
- TopBar.vue
- DashboardMockTransactions.vue
- DashboardMockLayout.md
- DashboardMock.md
- MockDataCanvas.md

#### Issues / TODOs

- ***
