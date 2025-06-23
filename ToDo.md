# pyNance Frontend - Site Map & Issue Tracker (`frontend/src/views/`)

---

## Dashboard.vue

### Components

- `Title & Greeting`
  - Update styling to be in line with expected title & greeting
  - Theme the username a different color
  - Lines should be different font size
  - The custom message on the third row should update based on the total net worth of the user
    - Below $0 shows concerned message
    - Above $1,000 shows encouraging message etc.
    - Message should be amusing, sarcastic, humorous, even insulting
- `Account Snapshot`
  - Theme the Account Snapshot title to demonstrate it is a distinct module/section
  - The 'configure' button should be themed to match design
  - The submenu (Select up to 5 accounts) should be themed as a dropdown
  - The configuration button should be a fuzzyfind supported dropdown menu selection
  - Currently it does not display anything. This broken module needs to be fixed and styled per above
  - The Account Snapshot should display additional information in line with what a user would expect a snapshot to display
- `Daily Net Income Chart`
  - This chart currently does not display any information and needs to be fixed
  - The axis labels are too small and are difficult to read
  - The legend is not necessary, everyone knows that green is positive and red is negative
- `Spending by Category Chart` -- Requested
  - This chart does not show any data and needs to be fixed
  - The axis labels are too small and are difficult to read
  - The title should be styled to illustrate that it is the title
  - The legend / category selectors take up far too much of the visual. They should be moved to an expandable / collapsible tab
  - The category selectors should fuzzy find / match on existing categories
  - The axis labels overlap into the transactions table below. This needs to be fixed with tailwindcss stylings
- `Accounts Tables`
  - The table needs the Balance column to be styled with accounting style ($2,000.51) parenthesis, dollar sign, red font for negative balance (and liabilities with positive balance)
  - Account type should have uniform capitalization - normalize to capitalize first letter of each word
  - Normalize Account Name as well
  - Need columns spaced to fit all on one line per entry
  - Think about adding Plaid Institution Icon per line item for different institutions
  - Table needs to be paginated and/or scrollable

#### Issues / TODOs

- ***

## Accounts.vue

### Components

- `Header Greeting`
  - Update styling for different font sizes
  - Colorize fonts to be in theme
- `Link Account Section`
  - Menu should be an expandable / collapsible dropdown with selection visible on expanded view
  - 'Refresh Plaid/Teller' subtitles should be styled and themed
  - Date selectors, Account Selectors, Refresh Buttons should be styled and themed
  - Layout should be designed with aesthetics
  - Products Selection should have Teller products selection
  - There is no Link Account button. It should be in the same section as the Select Products. Button only clickable if a product is selected
  - This whole section is collapse/expandable
- `Assets Year Comparison Chart`
  - Currently has no display
- `Net Assets Trend Chart`
  - Currently has no display

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
