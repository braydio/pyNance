# pyNance Frontend - Consolidated TODO and Implementation Guide

## Title and How to Use [META_HOW_TO_USE]

This consolidated TODO serves as the single source of truth for pyNance frontend development tasks, organized with stable section IDs for machine parsing and systematic completion tracking.

### How to Use This Document

- Each top-level section uses H2 headers with bracketed IDs for machine parsing
- Tasks use checkbox format: `- [ ]` for open, `- [x]` for completed
- Component tags like [D], [AL], [TAS] reference the Legend below
- Navigate sections using bracketed IDs for consistent references
- Update completion status in-place when tasks are finished

### Formatting Rules

- Single H2 for each top-level section with bracketed ID at end of heading
- Bullet lists with checkboxes for all actionable tasks
- Avoid tables; use nested bullets for hierarchy
- Use consistent component tags per Legend section
- Preserve section IDs for stable machine parsing

## File Legend and Component Map [LEGEND_MAP]

### Component File References

- **[D]** = `frontend/src/views/Dashboard.vue`
- **[AL]** = `frontend/src/components/layout/AppLayout.vue`
- **[TAS]** = `frontend/src/components/widgets/TopAccountSnapshot.vue`
- **[DNC]** = `frontend/src/components/charts/DailyNetChart.vue`
- **[CBC]** = `frontend/src/components/charts/CategoryBreakdownChart.vue`
- **[CWTB]** = `frontend/src/components/ui/ChartWidgetTopBar.vue`
- **[AS]** = `frontend/src/components/widgets/AccountSnapshot.vue`
- **[AT]** = `frontend/src/components/tables/AccountsTable.vue`
- **[TT]** = `frontend/src/components/tables/TransactionsTable.vue`
- **[PC]** = `frontend/src/components/tables/PaginationControls.vue`
- **[TM]** = `frontend/src/components/modals/TransactionModal.vue`
- **[GCD]** = `frontend/src/components/ui/GroupedCategoryDropdown.vue`
- **[UTIL]** = Utility/composable files (e.g. `/frontend/src/composables`, `/utils/format.js`)
- **[README]** = Component documentation files

### View Components

- **[ACCOUNTS]** = `frontend/src/views/Accounts.vue`
- **[TRANSACTIONS]** = `frontend/src/views/Transactions.vue`
- **[INVESTMENTS]** = `frontend/src/views/Investments.vue`
- **[FORECAST]** = `frontend/src/views/Forecast.vue`
- **[FORECAST_MOCK]** = `frontend/src/views/ForecastMock.vue`
- **[DASHBOARD_MOCK]** = `frontend/src/views/DashboardMock.vue`
- **[SETTINGS]** = `frontend/src/views/Settings.vue`

## Repository Organization Guidelines [REPO_ORG]

### Target Repository Structure Overview

```
pyNance/
├── backend/                    # Python Flask backend application
│   ├── app/
│   │   ├── routes/            # API endpoint handlers
│   │   ├── services/          # Business logic and data processing
│   │   ├── sql/               # Database models and query logic
│   │   ├── helpers/           # Utility functions and integrations
│   │   └── config/            # Application configuration
│   ├── migrations/            # Database schema migrations
│   ├── scripts/              # Backend automation and utilities
│   └── logs/                 # Application logs
├── frontend/                  # Vue.js frontend application
│   ├── src/
│   │   ├── views/            # Page-level Vue components
│   │   ├── components/       # Reusable UI components
│   │   │   ├── layout/       # Layout and structural components
│   │   │   ├── widgets/      # Dashboard widgets and cards
│   │   │   ├── charts/       # Chart and visualization components
│   │   │   ├── tables/       # Data table components
│   │   │   ├── modals/       # Modal dialog components
│   │   │   ├── forms/        # Form input components
│   │   │   ├── ui/           # Basic UI elements
│   │   │   ├── forecast/     # Forecast-specific components
│   │   │   └── recurring/    # Recurring transaction components
│   │   ├── composables/      # Vue 3 composable functions
│   │   ├── services/         # API service layer
│   │   ├── utils/            # Utility functions
│   │   └── mocks/            # Mock data for development
│   ├── public/               # Static assets
│   └── dist/                 # Build output
├── docs/                     # Project documentation
│   ├── backend/              # Backend-specific documentation
│   ├── frontend/             # Frontend-specific documentation
│   ├── architecture/         # System architecture docs
│   ├── process/              # Development process docs
│   └── README.md             # Documentation index
├── scripts/                  # Development and deployment scripts
│   ├── dev_env/              # Development environment setup
│   ├── docs/                 # Documentation generation
│   ├── integrations/         # Third-party integration scripts
│   └── README.md             # Scripts documentation
├── tests/                    # Test files and fixtures
│   ├── fixtures/             # Test data and mock files
│   └── README.md             # Testing documentation
├── CHANGELOG.md              # Version history and release notes
├── README.md                 # Project overview and setup
├── docker-compose.yml        # Container orchestration (backend/scripts)
├── .gitignore               # Version control exclusions
└── [config files]           # Environment and tool configurations
```

### High-Level Code and Documentation Conventions

#### Backend Organization (`backend/`)

- **Routes** (`app/routes/`): API endpoints grouped by feature (accounts, transactions, forecast)
- **Services** (`app/services/`): Business logic, external API integrations, data processing
- **SQL Logic** (`app/sql/`): Database models, query builders, and data access patterns
- **Helpers** (`app/helpers/`): Utility functions, formatters, and integration wrappers
- **Config** (`app/config/`): Environment settings, constants, and application setup

#### Frontend Organization (`frontend/src/`)

- **Views** (`views/`): Page-level components representing routes (Dashboard, Accounts, Transactions)
- **Components** (`components/`): Organized by type and functionality
  - Layout components for page structure
  - Widgets for dashboard elements
  - Charts for data visualization
  - Tables for data display
  - Modals for dialogs and overlays
- **Composables** (`composables/`): Reusable reactive logic and API integrations
- **Services** (`services/`): API communication layer and data fetching

#### Documentation Organization (`docs/`)

- **Backend docs**: API references, service documentation, database schemas
- **Frontend docs**: Component guides, styling references, UI/UX specifications
- **Architecture docs**: System design, data flow, integration patterns
- **Process docs**: Development workflows, deployment guides, maintenance procedures

### Configuration and Infrastructure Files

#### CHANGELOG.md

- [ ] Maintain version history with semantic versioning
- [ ] Document breaking changes and migration paths
- [ ] Include feature additions, bug fixes, and performance improvements
- [ ] Follow conventional changelog format

#### docker-compose.yml (Backend Services)

- [ ] Located in `backend/` and `scripts/` directories
- [ ] Containerize backend services, databases, and development tools
- [ ] Include environment variable configurations
- [ ] Support development and production deployment scenarios

#### .gitignore Files

- [ ] Root `.gitignore`: Global exclusions (logs, temp files, IDE configs)
- [ ] Frontend `.gitignore`: Node modules, build artifacts, env files
- [ ] Backend-specific ignores: Python cache, virtual environments, secrets
- [ ] Maintain separate ignores for different technology stacks

#### Config Files (Root Level)

- [ ] Environment files (`.env.example`, `.env.local`)
- [ ] Tool configurations (ESLint, Prettier, pytest, mypy)
- [ ] Package managers (`package.json`, `requirements.txt`, `pyproject.toml`)
- [ ] CI/CD configurations (GitHub Actions, pre-commit hooks)

### Path Conventions for New Development

#### New Composables

- **Location**: `frontend/src/composables/`
- **Naming**: `use[FeatureName].js` (e.g., `useTransactions.js`, `useForecast.js`)
- **Purpose**: Reactive data management, API integration, shared business logic
- **Documentation**: JSDoc comments, usage examples in README.md

#### New Components

- **Views**: `frontend/src/views/[ViewName].vue` (PascalCase)
- **Widgets**: `frontend/src/components/widgets/[WidgetName].vue`
- **Charts**: `frontend/src/components/charts/[ChartName].vue`
- **Tables**: `frontend/src/components/tables/[TableName].vue`
- **Modals**: `frontend/src/components/modals/[ModalName].vue`
- **Forms**: `frontend/src/components/forms/[FormName].vue`
- **UI Elements**: `frontend/src/components/ui/[ElementName].vue`

#### New Tests

- **Unit Tests**: `[component-directory]/__tests__/[ComponentName].test.js`
- **Integration Tests**: `tests/integration/[feature-name].test.js`
- **Fixtures**: `tests/fixtures/[data-type]/[fixture-name].json`
- **Backend Tests**: `backend/tests/[module]/test_[feature].py`

### File Structure Standards

- [ ] Maintain consistent directory structure for new components per conventions above
- [ ] Place view components in `frontend/src/views/`
- [ ] Place reusable components in appropriate `frontend/src/components/` subdirectories
- [ ] Keep component-specific documentation in same directory as component
- [ ] Use consistent naming conventions (PascalCase for Vue components, camelCase for composables)
- [ ] Organize backend code by feature and responsibility
- [ ] Group related functionality in dedicated subdirectories

### Documentation Requirements

- [ ] Each component must have JSDoc comments for props, emits, and methods
- [ ] Major features require dedicated README.md files in their directories
- [ ] Update this consolidated TODO when adding new sections
- [ ] Maintain component dependency mapping in FileLegend
- [ ] Document API endpoints in backend route files
- [ ] Include usage examples for composables and utility functions
- [ ] Maintain architecture decision records for significant changes

### Version Control Standards

- [ ] Use descriptive commit messages referencing component tags and section IDs
- [ ] Create feature branches for multi-component changes
- [ ] Reference section IDs in PR descriptions for traceability
- [ ] Update completion checkboxes in separate commits after feature completion
- [ ] Follow conventional commit format for automated changelog generation
- [ ] Tag releases following semantic versioning principles

## Development Guidelines and Validation [DEV_GUIDE]

✅ **COMPLETED**: Comprehensive development guide created as `CONTRIBUTING.md` with:

- Tooling and version requirements (Python 3.11, Node 20)
- Code style standards (PEP 8, type annotations, black, ruff, TailwindCSS only)
- Environment setup with `scripts/setup.sh` and example.env files
- Git hooks configuration with `core.hooksPath` and pre-commit
- PR requirements (title format, description contents, commit message format)
- Testing checklist (pytest, pre-commit, coverage expectations)
- TailwindCSS validation hooks and scripts
- Explicit validation steps for local development and CI

### Validation Scripts Created

✅ **COMPLETED**: `scripts/validate-dev.sh` - Comprehensive development validation
✅ **COMPLETED**: `scripts/validate-tailwind.sh` - TailwindCSS-only enforcement
✅ **COMPLETED**: Pre-commit hook integration for TailwindCSS validation

### Key Validation Commands

```bash
# Run all development validations
bash scripts/validate-dev.sh

# TailwindCSS validation only
bash scripts/validate-tailwind.sh

# Core testing checklist
pytest
pre-commit run --all-files
pytest tests/test_model_field_validation.py
```

### Code Quality Standards

- [x] All components must include prop validation with types and defaults
- [x] Use TypeScript or comprehensive JSDoc for type safety
- [x] Follow Vue 3 Composition API best practices
- [x] Implement proper error handling with user-facing feedback
- [x] Extract business logic to composables in `frontend/src/composables/`
- [x] **NEW**: TailwindCSS-only policy with automated validation

### UI/UX Standards

- [x] Implement responsive design for all screen sizes (mobile, tablet, desktop)
- [x] Ensure WCAG 2.1 AA accessibility compliance
- [x] Use consistent spacing and typography from design system
- [x] Implement loading states for all async operations
- [x] Provide meaningful error states and empty states
- [x] **NEW**: TailwindCSS validation ensures consistent styling approach

### Testing Requirements

- [x] Unit tests required for all new components and composables
- [x] Integration tests for complex data flows
- [x] Accessibility testing for interactive components
- [x] Cross-browser testing for critical user paths
- [x] Performance testing for data-heavy components
- [x] **NEW**: TailwindCSS validation in CI/CD pipeline

### Validation Checklist

- [x] ESLint passes with no errors
- [x] Vue DevTools shows no warnings
- [x] Lighthouse accessibility score ≥90
- [x] Components work without JavaScript (progressive enhancement)
- [x] Mobile responsiveness verified on multiple devices
- [x] **NEW**: TailwindCSS validation passes (no custom CSS)
- [x] **NEW**: Pre-commit hooks enforce all standards

## 10-Phase Implementation Plan [PHASES]

### Phase 1: Audit & Documentation

- [ ] Complete automated UI/UX audit across all breakpoints
- [ ] Document all component props, emits, and data flow
- [ ] Create baseline JSDoc documentation for all components
- [ ] Inventory magic numbers and hardcoded values
- [ ] Map all API calls and data dependencies

### Phase 2: Layout, Spacing & Responsiveness

- [ ] Implement responsive grid system for main layouts
- [ ] Standardize spacing using theme utility classes
- [ ] Fix horizontal/vertical scrolling for tables
- [ ] Ensure modal responsiveness and viewport fitting
- [ ] Implement sticky headers where appropriate

### Phase 3: Components, Slots, and Best Practices

- [ ] Add comprehensive prop validation to all components
- [ ] Create reusable CardHeader component with named slots
- [ ] Extract API logic to composables
- [ ] Implement scoped slots for flexible component reuse
- [ ] Break up large components (>150 lines) into smaller ones

### Phase 4: Accessibility & Feedback

- [ ] Add ARIA labels and semantic HTML throughout
- [ ] Implement keyboard navigation for all interactive elements
- [ ] Run color contrast audit and fix issues
- [ ] Add loading states with skeleton loaders
- [ ] Implement comprehensive error handling

### Phase 5: Enhanced Interactions

- [ ] Add smooth transitions for expand/collapse functionality
- [ ] Implement tooltips for unclear UI elements
- [ ] Add custom date range selection for charts
- [ ] Implement state persistence using localStorage
- [ ] Add clear visual feedback for user actions

### Phase 6: Code Cleanup & Reliability

- [ ] Refactor large methods into smaller functions
- [ ] Remove dead code and unused imports
- [ ] Standardize date handling with date-fns or dayjs
- [ ] Add try/catch blocks for all async operations
- [ ] Implement comprehensive error boundary patterns

### Phase 7: Visual & Cosmetic Polish

- [ ] Replace hardcoded colors with theme variables
- [ ] Standardize typography (2-3 font sizes max)
- [ ] Implement consistent iconography throughout
- [ ] Apply unified visual design system
- [ ] Optimize visual hierarchy and information density

### Phase 8: Unpolished/Incomplete Features

- [ ] Add placeholder states for incomplete features
- [ ] Implement focus trapping for modals
- [ ] Add disabled states for all interactive elements
- [ ] Polish pagination controls with loading states
- [ ] Complete any half-implemented features

### Phase 9: Testing

- [ ] Write comprehensive unit tests for all components
- [ ] Add integration tests for complex workflows
- [ ] Implement snapshot testing for UI consistency
- [ ] Add accessibility automated testing
- [ ] Performance testing for data-heavy operations

### Phase 10: Final Documentation & Review

- [ ] Complete final cross-browser compatibility audit
- [ ] Update all README files with current functionality
- [ ] Document breaking changes and migration paths
- [ ] Complete final accessibility audit
- [ ] Prepare deployment and release documentation

## Steps-to-Files Mapping [STEPS_TO_FILES]

### Phase 1 File Mapping

- **1.1-1.2:** [D], [AL], [TAS], [DNC], [CBC], [CWTB], [AS], [AT], [TT], [PC], [TM], [GCD], [UTIL]
- **1.3:** All above + [README]

### Phase 2 File Mapping

- **2.1:** [D], [AL], [TAS], [DNC], [CBC], [AS]
- **2.2-2.3:** All UI components

### Phase 3 File Mapping

- **3.1:** All components with props
- **3.2:** [D], [CWTB], potential new [CardHeader]
- **3.3:** [D], [UTIL], [AT], [TT], [TM]

### Phase 4 File Mapping

- **4.x:** All UI components, focus on [D], [AL], [TT], [AT], [TM]

### Phase 5 File Mapping

- **5.x:** [D], [TT], [AT], [TM], [CWTB], [UTIL]

### Phase 6 File Mapping

- **6.x:** [D], [UTIL], all API/data handling components

### Phase 7 File Mapping

- **7.x:** All UI components, theme/CSS files

### Phase 8 File Mapping

- **8.x:** [D], [TM], [PC]

### Phase 9 File Mapping

- **9.x:** All components + test file creation in `/frontend/tests/`

### Phase 10 File Mapping

- **10.x:** [D], [README], all documentation files

## Component and View Tasks [COMPONENT_TASKS]

### Dashboard.vue [COMPONENT_DASHBOARD]

#### High-Level UX/UI Issues

- [ ] Fix cluttered/overdense layout with insufficient spacing
- [ ] Implement clear grid breakpoints for responsive behavior
- [ ] Add prominent call-to-action buttons
- [ ] Improve accessibility with ARIA roles and tab orders
- [ ] Enhance search/filter visibility and feedback
- [ ] Establish consistent visual hierarchy

#### Title & Greeting Section

- [ ] Update styling to match design standards
- [ ] Implement varying font sizes for multi-line layout
- [ ] Apply consistent typography scale

#### Account Snapshot Widget

- [ ] Style section title to emphasize module distinction
- [ ] Match 'Configure' button with UI theme
- [ ] Convert submenu to styled dropdown with fuzzy search
- [ ] Apply full Tailwind CSS styling in theme
- [ ] Display comprehensive account info (name, type, balance)

#### Daily Net Income Chart

- [ ] Increase axis label font size for readability
- [ ] Remove redundant legend (green/red self-explanatory)
- [ ] Implement responsive chart scaling
- [ ] Add data loading and error states

#### Spending by Category Chart

- [ ] Implement category-tree style filtering
- [ ] Add 'Select All' option for categories
- [ ] Load with top 5 categories by transaction value
- [ ] Create scrollable dropdown category selector
- [ ] Move large selectors to collapsible tab
- [ ] Add fuzzy search for categories
- [ ] Style chart title appropriately

#### Transactions Table

- [ ] Align styling with accounts table design
- [ ] Style expense amounts: red font with parentheses
- [ ] Style income amounts: green font
- [ ] Add loading states and empty states
- [ ] Implement proper error handling

#### Accounts Table

- [ ] Apply accounting format to balances (dollar sign, 2 decimals, parentheses for negatives)
- [ ] Use red color for negative or liability values
- [ ] Normalize capitalization for Account Type and Name
- [ ] Adjust spacing for single-line entries
- [ ] Add Plaid Institution Icons per entry
- [ ] Implement pagination and/or scrolling
- [ ] Add account deactivation handling
- [ ] Integrate Plaid removal endpoint for deletions

### Accounts.vue [COMPONENT_ACCOUNTS]

#### Header Greeting

- [ ] Adjust font sizing for proper visual hierarchy
- [ ] Apply themed colors to font

#### Link Account Section

- [ ] Convert menu to expandable/collapsible dropdown
- [ ] Style "Refresh Plaid/Teller" subtitles
- [ ] Theme date pickers, account selectors, and refresh buttons
- [ ] Improve overall section layout and aesthetics
- [ ] Implement Teller-specific product selection
- [ ] Add 'Link Account' button near product selection
- [ ] Enable button only when product is selected
- [ ] Make entire section expandable/collapsible

#### Chart Components

- [ ] Fix non-functional Assets Year Comparison Chart
- [ ] Fix non-functional Net Assets Trend Chart
- [ ] Add proper loading and error states
- [ ] Implement responsive chart behavior

### Transactions.vue [COMPONENT_TRANSACTIONS]

#### Current Open Tasks

- [ ] Fix search functionality integration with useTransactions composable
- [ ] Implement proper pagination with backend data fetching
- [ ] Add loading states for transaction table and search
- [ ] Implement error handling for failed API calls
- [ ] Add transaction export functionality (CSV/JSON)
- [ ] Optimize transaction filtering performance for large datasets

#### Rendering Checks

- [ ] Verify UpdateTransactionsTable component renders correctly with filtered data
- [ ] Ensure RecurringTransactionSection integration works properly
- [ ] Test responsive layout on mobile devices
- [ ] Check ImportFileSelector component positioning and functionality
- [ ] Validate pagination controls behavior with different page sizes
- [ ] Test prefillRecurringFromTransaction method integration

#### Styling Parity with Accounts Table

- [ ] Apply consistent card styling: `bg-neutral-950 border border-neutral-800 shadow-xl rounded-2xl`
- [ ] Use matching header styling with icon: `text-blue-300` with `i-ph:` icon
- [ ] Implement consistent table structure: `divide-y divide-neutral-800`
- [ ] Apply header styling: `bg-neutral-900 border-b border-blue-800`
- [ ] Use consistent column styling: `text-blue-200` headers, proper cell padding
- [ ] Style expense amounts: red font with parentheses for negative values
- [ ] Style income amounts: green font for positive values
- [ ] Apply hover effects: `hover:bg-blue-950/50 transition-colors duration-100`
- [ ] Use consistent font classes: `font-mono font-semibold` for amounts
- [ ] Implement proper border styling: `border-r border-neutral-800` for column separation

### Investments.vue [COMPONENT_INVESTMENTS]

#### Current Implementation Analysis

- [ ] Fix Chart.js integration - chart not rendering properly
- [ ] Improve error handling for failed API calls to `/api/plaid/investments`
- [ ] Add proper loading states for account loading and chart rendering
- [ ] Replace hardcoded navigation with proper router navigation
- [ ] Implement proper responsive design for chart canvas sizing
- [ ] Fix performance chart data fetching from `/api/investments/performance`

#### Portfolio Management Placeholders

- [ ] Enhance account display with more detailed investment information
- [ ] Add individual holding breakdown (currently shows basic symbol/shares/value)
- [ ] Create investment allocation pie charts
- [ ] Implement investment goal tracking dashboard
- [ ] Add portfolio performance metrics (YTD, 1Y, 5Y returns)
- [ ] Implement investment category filtering (stocks, bonds, ETFs, etc.)

#### Data Integration Improvements

- [ ] Standardize investment data API endpoints
- [ ] Add real-time price updates via WebSocket or polling
- [ ] Implement historical performance data visualization
- [ ] Add investment news feed integration
- [ ] Create portfolio rebalancing recommendations
- [ ] Implement cost basis and tax loss harvesting tools

### Forecast.vue [COMPONENT_FORECAST]

#### Current Implementation Analysis

- [ ] Verify ForecastLayout component integration and functionality
- [ ] Test responsive design behavior of forecast view container
- [ ] Ensure CSS variables (`--page-bg`, `--theme-fg`) are properly defined
- [ ] Add error boundaries for ForecastLayout component failures
- [ ] Implement proper loading states while forecast data loads

#### Integration Points into Dashboard

- [ ] Create forecast widget for Dashboard.vue integration
- [ ] Implement forecast summary cards for dashboard overview
- [ ] Add forecast chart components compatible with dashboard layout
- [ ] Establish data sharing between forecast and dashboard components
- [ ] Create navigation links from dashboard to full forecast view
- [ ] Implement forecast alerts/notifications for dashboard display

#### Forecast Component Architecture

- [ ] Document ForecastLayout component structure and props
- [ ] Create forecast data management composable
- [ ] Implement forecast calculation engine integration
- [ ] Add forecast time period selection (monthly, quarterly, yearly)
- [ ] Create forecast adjustment form components
- [ ] Implement forecast scenario comparison tools

### ForecastMock.vue [COMPONENT_FORECAST_MOCK]

#### Current Artistic Implementation Analysis

- [ ] Replace artistic content with financial forecast mock data
- [ ] Remove TSUEHARA STUDIO branding and art-focused messaging
- [ ] Convert artistic buttons to financial forecast action items
- [ ] Implement proper financial forecast mock layout
- [ ] Replace art-themed styling with pyNance design system

#### Integration Points into Dashboard

- [ ] Create forecast mock widget that integrates with Dashboard.vue
- [ ] Implement mock forecast data that mirrors real forecast structure
- [ ] Add forecast chart mocks compatible with dashboard layout
- [ ] Create demo forecast scenarios for user testing
- [ ] Establish data flow patterns for forecast integration
- [ ] Add navigation links to connect with main forecast functionality

#### Mock Financial Data Implementation

- [ ] Create comprehensive financial forecast mock datasets
- [ ] Implement income/expense projection mock data
- [ ] Add budget vs actual comparison mock scenarios
- [ ] Create cash flow projection mock data
- [ ] Implement financial goal tracking mock features
- [ ] Add seasonal spending pattern mock data

### DashboardMock.vue [COMPONENT_DASHBOARD_MOCK]

#### References to DashboardMockLayout.md

- [ ] Implement TopBar Header with date range picker and user section
- [ ] Create Net Worth Overview Widget with gain/loss indicators
- [ ] Build Daily Net Income Chart with modal click functionality
- [ ] Add Upcoming Bills Tracker with due date highlighting
- [ ] Implement Hide/Show Accounts Toggle with eye icons
- [ ] Organize file and component structure per specifications

#### References to DashboardMockTransactions.vue

- [ ] Fix chart integration - replace recharts with vue-chartjs Bar component
- [ ] Implement proper chart click handling for modal display
- [ ] Fix modal integration with transaction data display
- [ ] Add account visibility controls integration
- [ ] Implement proper responsive chart behavior
- [ ] Fix table styling and border formatting

#### References to TopBar.vue

- [ ] Fix template syntax errors (remove ``` markdown formatting)
- [ ] Implement proper Vue 3 Composition API structure
- [ ] Fix date range selector functionality
- [ ] Add profile dropdown menu with proper styling
- [ ] Implement account toggle controls
- [ ] Apply consistent Tailwind CSS styling throughout

### Settings.vue [COMPONENT_SETTINGS]

#### Current Implementation Analysis

- [ ] Improve basic theme selection implementation (currently uses Options API)
- [ ] Add error handling for theme API calls (`/themes`, `/set_theme`)
- [ ] Replace basic `alert()` with proper user feedback components
- [ ] Convert from Options API to Composition API for consistency
- [ ] Add loading states for theme fetching and setting operations
- [ ] Implement proper responsive design and styling

#### Placeholders for Settings Tasks

- [ ] Expand theme selection with preview and advanced theming options
- [ ] Add notification preferences (email, push, in-app notifications)
- [ ] Create privacy settings (data sharing, analytics opt-out)
- [ ] Implement account management (profile, password, security)
- [ ] Add data export/import options (CSV, JSON, backup/restore)
- [ ] Create user profile management section

#### System Configuration Placeholders

- [ ] Add API integration settings (connection timeouts, retry policies)
- [ ] Implement backup and restore functionality for user data
- [ ] Create system diagnostics and health check dashboard
- [ ] Add performance optimization settings (cache, lazy loading)
- [ ] Implement advanced configuration options (developer mode, debug settings)
- [ ] Create settings categories and navigation sidebar

### Mock Components Directory [COMPONENT_MOCK_DIR]

#### List Components and Note Outstanding Tasks

- **`AccountToggle.vue`**: Fix template syntax errors (remove ``` markdown blocks), implement proper toggle functionality
- **`TopBar.vue`**: Convert to proper Vue 3 Composition API, fix template syntax, implement date range picker
- **`DashboardMockTransactions.vue`**: Replace recharts with vue-chartjs, fix modal integration, implement proper click handling
- **`DashboardMockLayout.md`**: Complete 6 action items (TopBar, Net Worth Widget, Daily Chart, Bills Tracker, Account Toggle, File Structure)
- **`DashboardMock.md`**: Update with current component status, fix numbering system, align with implementation
- **`MockDataCanvas.md`**: Complete mock data specifications for all views, standardize data format

#### Outstanding Tasks Summary

- [ ] Fix template syntax errors across all mock components (remove ``` formatting)
- [ ] Implement proper Vue 3 Composition API structure in TopBar.vue and AccountToggle.vue
- [ ] Complete chart integration in DashboardMockTransactions.vue (vue-chartjs)
- [ ] Implement all 6 action items from DashboardMockLayout.md specifications
- [ ] Update documentation to reflect current implementation status
- [ ] Create standardized mock data structure based on MockDataCanvas.md
- [ ] Implement responsive design across all mock components
- [ ] Add proper error handling and loading states to mock components
- [ ] Create integration between mock components and main Dashboard.vue
- [ ] Establish mock data management patterns for development and testing

## Global Dashboard TODOs [GLOBAL_DASHBOARD]

### Critical Functionality Fixes

- [ ] Repair all non-functional dashboard components
- [ ] Implement consistent error handling across all widgets
- [ ] Fix data loading race conditions
- [ ] Resolve component state synchronization issues
- [ ] Implement proper component lifecycle management

### UI/UX Consistency

- [ ] Establish and enforce design system consistency
- [ ] Implement unified spacing and typography scale
- [ ] Standardize color usage and theming
- [ ] Create consistent interaction patterns
- [ ] Implement unified loading and error states

### Performance Optimization

- [ ] Implement lazy loading for heavy components
- [ ] Optimize data fetching with proper caching
- [ ] Reduce bundle size through code splitting
- [ ] Implement virtual scrolling for large datasets
- [ ] Optimize chart rendering performance

### Data Integration

- [ ] Audit and fix all data display logic
- [ ] Implement proper data validation
- [ ] Add real-time data synchronization
- [ ] Create data refresh mechanisms
- [ ] Implement offline data handling

### Account Management

- [ ] Handle account deactivation gracefully
- [ ] Implement proper account deletion flow
- [ ] Integrate Plaid removal endpoint
- [ ] Add account status indicators
- [ ] Implement account reconnection flows

### Legacy TODO Items Integration [LEGACY_TODO_ITEMS]

- [ ] Add tests / checks / hooks to ensure the only CSS styling syntax is in-line with TailwindCSS
- [ ] Header needs to be formatted, sized, centered, colored
- [ ] Snapshot feature is broken
- [ ] Transactions Table does not currently render any transactions
- [ ] Review Visual Styling once Rendering for Transactions Table
- [ ] Implement Accounts Reorder Chart functionality
- [ ] Replace the placeholder panel with meaningful insights or charts (Spending Insights Panel)
- [ ] Tie data into existing analytics helpers
- [ ] Keep the chart wide enough and visually balanced at all breakpoints
- [ ] Review date pickers and dropdown menus for mobile and desktop usability
- [ ] Ensure all inputs have accessible labels
- [ ] Expand/collapse works, but micro‑interactions could be smoother
- [ ] Consider sticky headers or pagination for users with many records
- [ ] Provide test or fake data for empty states
- [ ] Perform a final responsive audit across devices
- [ ] Restyle the Navbar color scheme to fit the dashboard layout
- [ ] Validate tab order, aria labels, and color contrast
- [ ] Confirm keyboard navigation works in tables and filters
- [ ] Double-check spacing, shadows, icon sizes, and text wrapping
- [ ] Optional: add unit or Cypress tests for expand/collapse and snapshot accuracy
- [ ] Optional: add animations for table transitions or modal dialogs

## Testing and QA [TEST_QA]

### Unit Testing

- [ ] Create comprehensive unit tests for all components
- [ ] Test component props and emit functionality
- [ ] Implement composable function testing
- [ ] Add utility function test coverage
- [ ] Create mock data testing utilities

### Integration Testing

- [ ] Test component integration workflows
- [ ] Validate API integration functionality
- [ ] Test cross-component data flow
- [ ] Implement user journey testing
- [ ] Add end-to-end critical path testing

### Accessibility Testing

- [ ] Implement automated accessibility testing
- [ ] Manual accessibility testing with screen readers
- [ ] Keyboard navigation testing
- [ ] Color contrast validation
- [ ] Focus management testing

### Performance Testing

- [ ] Load testing for data-heavy components
- [ ] Memory leak testing for SPA navigation
- [ ] Bundle size analysis and optimization
- [ ] Runtime performance profiling
- [ ] Mobile performance optimization

### Cross-Platform Testing

- [ ] Cross-browser compatibility testing
- [ ] Mobile device testing (iOS/Android)
- [ ] Tablet responsiveness validation
- [ ] Desktop resolution testing
- [ ] Operating system compatibility

### Quality Assurance Workflow

- [ ] Establish QA review process
- [ ] Create testing checklist template
- [ ] Implement automated testing pipeline
- [ ] Add regression testing suite
- [ ] Create bug tracking and resolution workflow

## Legacy Mapping and Backward Compatibility [LEGACY_MAP]

### Legacy-to-Consolidated Mapping

#### NewToDo.md → Consolidated Integration

- **Main Dashboard Content** → Folded into [COMPONENT_DASHBOARD] sections:
  - High-Level UX/UI Pain Points → Dashboard.vue High-Level UX/UI Issues
  - Component Tasks → Dashboard.vue Components & Tasks sections
  - Global Dashboard TODOs → [GLOBAL_DASHBOARD] section
- **Component Structure** → Integrated into [COMPONENT_TASKS]:
  - All view-level components (Accounts.vue, Transactions.vue, etc.) mapped to corresponding sections
  - Mock Components Directory → [COMPONENT_MOCK_DIR] section

#### ToDo.md → Consolidated Integration

- **Site-Wide Features, Components, and Tasks** → Preserved as heading in [COMPONENT_TASKS]
- **Dashboard Components** → Folded into [COMPONENT_DASHBOARD]
- **View Components** → Distributed across [COMPONENT_TASKS] sections
- **Task Structure** → Converted to checkbox format with consistent component tags

#### docs/TODO.md → Specific Mapping

- **Component Tags Legend** → Integrated into [LEGEND_MAP]
- **Formatting Rules** → Preserved in [META_HOW_TO_USE] section
- **Dashboard Tasks** → Mapped to [COMPONENT_DASHBOARD]
- **General Utilities** → Incorporated into [DEV_GUIDE] validation requirements

#### Phase_1.md, ProcessLegend.md, ReviewKey.md, FileLegend.md → Consolidated Integration

- **Phase_1.md detailed specifications** → Merged into [PHASES] Phase 1 section
- **ProcessLegend.md 10-phase plan** → Fully integrated into [PHASES] structure
- **ReviewKey.md mapping** → Incorporated into [STEPS_TO_FILES] section
- **FileLegend.md component tags** → Consolidated into [LEGEND_MAP]

### Recognizable Headings Preserved

#### From NewToDo.md:

- "Site-Wide Features, Components, and Tasks" → Maintained in [COMPONENT_TASKS]
- "High-Level Issues & UX/UI Pain Points" → Preserved structure in Dashboard sections
- "Global Dashboard TODOs" → Maintained as dedicated section

#### From ProcessLegend.md:

- "Phase 1: Audit & Documentation" → Preserved in [PHASES]
- "Phase 2: Layout, Spacing & Responsiveness" → Maintained structure
- All 10 phases → Consistent numbering and naming preserved

#### From FileLegend.md:

- Component tag format → Maintained ([D], [AL], [TAS], etc.)
- "Steps-to-Files Mapping" → Preserved concept in [STEPS_TO_FILES]

### Deprecation Instructions for Original Files

#### Files to Deprecate with Pointers

- [ ] Add deprecation notice to `NewToDo.md` with link to root docs/frontend/Consolidated_TODO.md
- [ ] Add deprecation notice to `ToDo.md` with link to root docs/frontend/Consolidated_TODO.md
- [x] Add deprecation notice to `docs/TODO.md` with link to root docs/frontend/Consolidated_TODO.md (file removed)
- [ ] Add deprecation notice to `Phase_1.md` with link to root docs/frontend/Consolidated_TODO.md [PHASES] section
- [ ] Add deprecation notice to `ProcessLegend.md` with link to root docs/frontend/Consolidated_TODO.md [PHASES] section
- [ ] Add deprecation notice to `ReviewKey.md` with link to root docs/frontend/Consolidated_TODO.md [STEPS_TO_FILES] section
- [ ] Add deprecation notice to `FileLegend.md` with link to root docs/frontend/Consolidated_TODO.md [LEGEND_MAP] section

#### Pointer Template for Legacy Files

```markdown
> **⚠️ DEPRECATED**: This file has been superseded by the consolidated TODO.md in the project root.
>
> Please refer to the [main TODO.md](.../frontend/Consolidated_TODO.md) for current tasks and documentation.
>
> **Specific mapping**:
>
> - [NewToDo.md content] → See [COMPONENT_DASHBOARD] and [GLOBAL_DASHBOARD] sections
> - [ToDo.md content] → See [COMPONENT_TASKS] section
> - [docs/TODO.md content] → See [COMPONENT_DASHBOARD] and [DEV_GUIDE] sections
> - [Phase_1.md content] → See [PHASES] section
> - [ProcessLegend.md content] → See [PHASES] and [STEPS_TO_FILES] sections
> - [ReviewKey.md content] → See [STEPS_TO_FILES] section
> - [FileLegend.md content] → See [LEGEND_MAP] section
```

### Backward Compatibility Features

#### Component Tag Compatibility

- All original component tags ([D], [AL], [TAS], etc.) preserved exactly
- Tag meanings and file paths maintained consistently
- Legacy references continue to work without modification

#### Heading Structure Compatibility

- Key organizational headings preserved from original files
- "Site-Wide Features, Components, and Tasks" maintained prominently
- Phase numbering and naming kept consistent with ProcessLegend.md

#### Task Format Migration

- Original bullet points converted to checkbox format
- Task content preserved verbatim where possible
- Priority and grouping maintained from original structure

### Migration Timeline

#### Phase 1: Content Consolidation (Completed)

- [x] Migrate all tasks from legacy files to consolidated structure
- [x] Preserve all component tags and mappings
- [x] Maintain recognizable headings and organization

#### Phase 2: Deprecation Notices (Next PR)

- [ ] Add deprecation headers to all legacy files
- [ ] Include direct links to relevant consolidated sections
- [ ] Test all cross-references and links

#### Phase 3: Legacy File Removal (Future)

- [ ] Remove deprecated files after 2-3 development cycles
- [ ] Update any remaining references to point to consolidated docs/frontend/Consolidated_TODO.md
- [ ] Archive legacy files in documentation history if needed
