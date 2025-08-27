> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
> 
> Please refer to the [main TODO.md](../frontend/Consolidated_TODO.md) for current tasks and documentation.
> 
> **Specific mapping**:
> - Site Map & Issue Tracker → See [COMPONENT_TASKS] section
> - High-Level Issues & UX/UI Pain Points → See [COMPONENT_DASHBOARD] High-Level UX/UI Issues
> - All view components → See corresponding [COMPONENT_*] sections
> - Global Dashboard TODOs → See [GLOBAL_DASHBOARD] section

---

# pyNance Frontend - Legacy Content

- Site Map & Issue Tracker (`frontend/src/views/`)

---

- Site-Wide Features, Components, and Tasks

---

## Dashboard.vue

## High-Level Issues & UX/UI Pain Points

- Cluttered/Overdense Layout
  - Cards, widgets, and table sections are packed with minimal spacing.
  - Card "frames" have insufficient visual separation, making the dashboard feel cramped.
  - Insufficient whitespace/padding.
  - Responsiveness / Mobile
  - No clear grid breakpoints or column stacking (especially for charts + tables).
  - Some classes (e.g., max-w-5xl) may limit scaling on larger or smaller screens.
- Navigation & CTA
  - The only clear CTA is "zoom in/out" on the chart; no "add", "export", or "customize" button.
  - No prominent call-to-action for "Add Transaction" or quick links to other features.
- Accessibility
  - Color-only cues for charts/amounts—may be unreadable for colorblind users.
  - No ARIA roles, alt text, or tab orders for interactive elements.
- Search/Filter
  - Search bar and sort order are visually buried below charts and do not stand out.
  - Not enough feedback (e.g., "No results found" is not visually highlighted ).
- Card/Widget Titles
  - Lacks consistent and prominent section headers.
  - Some sections use ambiguous labels ("Net Total:") that can be more descriptive.
- Consistency
  - Inconsistent button sizing and style between widgets (e.g., the "Zoom In/Out" button).
  - Text sizing on headers, chart axes, and table columns varies a lot.
- Visual Hierarchy
  - Difficult to quickly identify most important data (e.g., "Net Worth", "Today's Spending").
  - No strong color, size, or contrast hierarchy.

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
