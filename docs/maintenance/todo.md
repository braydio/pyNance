> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - Site-Wide Features, Components, and Tasks → See [COMPONENT_TASKS] section
> - Dashboard.vue content → See [COMPONENT_DASHBOARD] section
> - All view components → See corresponding [COMPONENT_*] sections
> - Global Dashboard TODOs → See [GLOBAL_DASHBOARD] section

---

# pyNance Frontend - Site Map & Issue Tracker (`frontend/src/views/`) - Legacy Content

---

# Site-Wide Features, Components, and Tasks

# Dashboard.vue

## --

### Components & Tasks

#### Title & Greeting

- Update styling to match design standards.
- Use varying font sizes for multi-line layout.

#### Account Snapshot

- Style section title to emphasize module distinction.

- Match 'Configure' button with UI theme.
- Submenu ("Select up to 5 accounts") should be a styled dropdown.
- Enable fuzzy find functionality in dropdown.
- Section needs to be tailwindcss styled in full and in theme
- Show relevant snapshot info: account name, type, balance, etc.

#### Daily Net Income Chart

- Axis label font size increased for readability. (Unverified)
- Legend removed (green/red is self-explanatory). (Unverified)

#### Spending by Category Chart _(Requested)_

- This should be Category-Tree style category filtering. Support for General Category Selection , Detailed Subcategory Selection without duping.
- Needs a 'Select All' option for categories.
- Should load with top 5 categories (by total transaction value) rendered.
- Category selector should be scrollable dropdown menu
- Style the chart title appropriately.
- Legend and category selectors are too large:
  - Move to a collapsible tab.
  - Add fuzzy search for categories.

#### Transactions Table

- Displays data correctly
- Table styling should be more in line with the accounts table below
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
- Properly handle account deactivation + deletions
- Integrate the Plaid removal endpoint upon deletion in the Accounts table

---

## Accounts.vue

### Components & Tasks

#### Header Greeting

- Adjust font sizing for visual hierarchy.
- Apply themed colors to font.

#### Link Account Section

- Make menu an expandable/collapsible dropdown.
- Style "Refresh Plaid" subtitles.
- Style and theme: date pickers, account selectors, refresh buttons.
- Improve section layout and aesthetic.
- Implement Plaid product selection improvements.
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
