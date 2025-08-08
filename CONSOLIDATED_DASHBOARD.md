# [COMPONENT_DASHBOARD] - Consolidated Dashboard.vue Tasks

## High-Level Issues and UX/UI Pain Points

### Layout and Visual Hierarchy
- [ ] **Fix cluttered/overdense layout** - Cards, widgets, and table sections are packed with minimal spacing
  - **Acceptance criteria:** Minimum 1rem spacing between major sections, clear visual separation between cards
- [ ] **Add insufficient whitespace/padding** - Card "frames" have insufficient visual separation
  - **Acceptance criteria:** Consistent padding applied using theme utilities, visual breathing room established
- [ ] **Establish clear visual hierarchy** - Difficult to quickly identify most important data (Net Worth, Today's Spending)
  - **Acceptance criteria:** Primary data elements use larger font sizes, strong color contrast, consistent information density

### Responsiveness and Breakpoints
- [ ] **Implement clear grid breakpoints** - No clear column stacking for charts and tables
  - **Acceptance criteria:** Responsive grid system works on mobile (320px+), tablet (768px+), desktop (1024px+)
- [ ] **Fix responsive scaling issues** - Some classes (e.g., max-w-5xl) may limit scaling on different screens
  - **Acceptance criteria:** Dashboard adapts fluidly across all viewport sizes, no horizontal scrolling on mobile

### Navigation and Call-to-Actions
- [ ] **Add prominent call-to-action buttons** - Only clear CTA is "zoom in/out" on chart
  - **Acceptance criteria:** "Add Transaction", "Export Data", "Customize View" buttons prominently displayed
- [ ] **Improve navigation clarity** - No quick links to other features
  - **Acceptance criteria:** Quick navigation menu accessible, clear visual hierarchy for action items

### Accessibility Gaps
- [ ] **Implement ARIA roles and attributes** - Missing ARIA roles, alt text, or tab orders for interactive elements
  - **Acceptance criteria:** All interactive elements have proper ARIA labels, screen reader compatible
- [ ] **Add keyboard navigation support** - No keyboard navigation for interactive elements
  - **Acceptance criteria:** All interactive elements accessible via keyboard, proper focus management
- [ ] **Fix color-only cues** - Charts/amounts may be unreadable for colorblind users
  - **Acceptance criteria:** Color contrast ratio ≥4.5:1, supplementary visual indicators beyond color

### Search and Filter UX
- [ ] **Improve search/filter visibility** - Search bar and sort order visually buried below charts
  - **Acceptance criteria:** Search controls prominently placed, clear visual hierarchy
- [ ] **Enhanced feedback mechanisms** - "No results found" not visually highlighted
  - **Acceptance criteria:** Clear feedback for empty states, loading states, and error conditions

### Component Consistency
- [ ] **Standardize component titles** - Lacks consistent and prominent section headers
  - **Acceptance criteria:** Uniform heading styles, descriptive section labels, consistent typography scale
- [ ] **Fix inconsistent button styles** - Inconsistent sizing and style between widgets
  - **Acceptance criteria:** All buttons follow unified design system, consistent hover/focus states

## Components and Tasks

### Title and Greeting Section [TAS]
- [ ] **Update typography to match design standards** - Apply consistent font sizing and theming
  - **Acceptance criteria:** Typography follows established scale, proper font weights applied
- [ ] **Implement multi-line layout with varying font sizes** - Improve visual hierarchy
  - **Acceptance criteria:** Multi-line text flows properly on all screen sizes, appropriate line heights

### Account Snapshot Widget [AS]
- [ ] **Apply themed styling to section title** - Emphasize module distinction
  - **Acceptance criteria:** Section headers clearly distinguish different dashboard modules
- [ ] **Style Configure button to match UI theme** - Consistent with overall design system
  - **Acceptance criteria:** Button follows theme colors, spacing, and interaction states
- [ ] **Convert submenu to styled dropdown** - "Select up to 5 accounts" should be styled dropdown
  - **Acceptance criteria:** Dropdown opens/closes smoothly, follows design system styling
- [ ] **Enable fuzzy find functionality in dropdown** - Improve account selection UX
  - **Acceptance criteria:** Users can type to filter accounts, search is case-insensitive
- [ ] **Apply full Tailwind CSS styling** - Complete theming integration
  - **Acceptance criteria:** No custom CSS, all styling uses Tailwind classes, theme variables applied
- [ ] **Display comprehensive account information** - Show account name, type, balance, etc.
  - **Acceptance criteria:** All relevant account data displayed, formatted consistently with accounting standards

### Daily Net Income Chart [DNC]
- [ ] **Increase axis label font size for readability** - Improve chart accessibility
  - **Acceptance criteria:** Axis labels readable at 12px minimum, clear visual hierarchy
- [ ] **Remove redundant legend** - Green/red color coding is self-explanatory
  - **Acceptance criteria:** Chart displays without legend, colors remain accessible, space better utilized
- [ ] **Implement responsive chart scaling** - Ensure chart works on all screen sizes
  - **Acceptance criteria:** Chart maintains aspect ratio and readability across all breakpoints
- [ ] **Add loading and error states** - Proper data state management
  - **Acceptance criteria:** Loading skeleton displays, error states show retry options

### Spending by Category Chart [CBC]
- [ ] **Implement category-tree style filtering** - Support General and Detailed Subcategory selection without duplication
  - **Acceptance criteria:** Hierarchical category selection, no duplicate transaction counting
- [ ] **Add 'Select All' option for categories** - Bulk selection functionality
  - **Acceptance criteria:** Single click selects/deselects all categories, clear visual feedback
- [ ] **Load with top 5 categories by default** - Show highest transaction value categories
  - **Acceptance criteria:** Dashboard loads showing 5 highest-value categories, others available via dropdown
- [ ] **Create scrollable dropdown category selector** - Manage large category lists
  - **Acceptance criteria:** Dropdown scrolls smoothly, maintains selection state, supports keyboard navigation
- [ ] **Move large selectors to collapsible tab** - Reduce visual obstruction
  - **Acceptance criteria:** Category selectors collapse/expand without affecting chart, smooth transitions
- [ ] **Add fuzzy search for categories** - Improve category finding
  - **Acceptance criteria:** Search filters categories in real-time, handles typos, case-insensitive
- [ ] **Style chart title appropriately** - Consistent with design system
  - **Acceptance criteria:** Title follows typography scale, proper spacing, theme colors

### Transactions Table [TT]
- [ ] **Fix data rendering issues** - Ensure all transactions display correctly
  - **Acceptance criteria:** All transaction data loads and displays, no rendering errors
- [ ] **Align styling with AccountsTable** - Maintain design consistency
  - **Acceptance criteria:** Both tables use identical styling patterns, spacing, and formatting
- [ ] **Apply accounting coloring rules to amounts** - Visual distinction for income/expenses
  - **Acceptance criteria:** Expenses show as red with parentheses (e.g., ($1,250.00)), income shows as green
- [ ] **Add loading states and empty states** - Proper state management
  - **Acceptance criteria:** Loading skeletons display, empty states show helpful messaging
- [ ] **Implement error handling** - Graceful failure handling
  - **Acceptance criteria:** Error states show retry options, clear error messaging for users

### Accounts Table [AT]
- [ ] **Apply accounting format to balances** - Dollar sign, 2 decimals, parentheses for negatives
  - **Acceptance criteria:** All monetary values follow standard accounting format ($X,XXX.XX)
- [ ] **Use red color for negative/liability values** - Visual indicators for account status
  - **Acceptance criteria:** Negative balances and liability accounts display in red, positive in default color
- [ ] **Normalize capitalization** - Consistent formatting for Account Type and Name
  - **Acceptance criteria:** Title case for names, consistent capitalization throughout
- [ ] **Adjust spacing for single-line entries** - Optimize table density
  - **Acceptance criteria:** All account entries fit on single line, proper row height, no text wrapping
- [ ] **Add Plaid Institution Icons** - Visual identification per entry
  - **Acceptance criteria:** Institution logos display consistently, fallback for unknown institutions
- [ ] **Implement pagination and/or scrolling** - Handle large account lists
  - **Acceptance criteria:** Tables with >10 entries show pagination or virtual scrolling, smooth performance
- [ ] **Add sticky headers at breakpoints** - Improve usability during scrolling
  - **Acceptance criteria:** Table headers remain visible during vertical scroll on desktop/tablet

## Global Dashboard TODOs

### Critical Functionality Fixes
- [ ] **Repair non-functional components** - Ensure all dashboard widgets work correctly
  - **Acceptance criteria:** Every dashboard component loads data and displays without errors
- [ ] **Fix data loading race conditions** - Resolve component initialization issues
  - **Acceptance criteria:** Components load data in correct order, no dependency conflicts

### UI/UX Refactoring
- [ ] **Refactor for consistent UI/UX** - Establish unified design patterns
  - **Acceptance criteria:** All components follow same design system, consistent spacing and typography
- [ ] **Establish design system consistency** - Unified visual language
  - **Acceptance criteria:** Color usage, spacing, and typography consistent across all components

### Data Management
- [ ] **Audit data display logic per component** - Ensure accurate data representation
  - **Acceptance criteria:** All displayed values are mathematically correct, consistent formatting
- [ ] **Implement proper data validation** - Prevent display of invalid data
  - **Acceptance criteria:** Invalid data handled gracefully, clear error messages for users

### Account Lifecycle Management
- [ ] **Handle account deactivation properly** - Graceful handling of disabled accounts
  - **Acceptance criteria:** Deactivated accounts clearly marked, excluded from calculations where appropriate
- [ ] **Handle account deletions** - Clean removal from all dashboard components
  - **Acceptance criteria:** Deleted accounts removed from all views, historical data preserved where needed
- [ ] **Integrate Plaid removal endpoint** - Complete account deletion workflow
  - **Acceptance criteria:** Plaid connections severed when accounts deleted, API cleanup completed

### Performance and Reliability
- [ ] **Implement component state synchronization** - Ensure consistent data across widgets
  - **Acceptance criteria:** Changes in one component reflect immediately in related components
- [ ] **Add comprehensive error handling** - Consistent error management
  - **Acceptance criteria:** All API failures handled gracefully, user-friendly error messages

## Acceptance Criteria Summary

### Keyboard Navigation Requirements
- [ ] All interactive elements accessible via Tab key
- [ ] Enter/Space keys activate buttons and links
- [ ] Arrow keys navigate within complex components (dropdowns, tables)
- [ ] Escape key closes modals and dropdowns
- [ ] Focus indicators clearly visible on all interactive elements

### ARIA Attributes Requirements
- [ ] All buttons have aria-label or aria-labelledby
- [ ] Tables use proper table markup with th/td elements
- [ ] Charts have aria-label describing the data
- [ ] Loading states use aria-live regions
- [ ] Form controls have associated labels

### Sticky Headers Verification at Breakpoints
- [ ] Desktop (≥1024px): Table headers stick during vertical scroll
- [ ] Tablet (768-1023px): Headers remain visible, no horizontal scroll
- [ ] Mobile (320-767px): Headers adapt to smaller screen, stack appropriately

### Component Integration Testing
- [ ] Account selection in snapshot reflects in related charts
- [ ] Date range changes affect all time-based components
- [ ] Category filters apply consistently across all visualizations
- [ ] Data refresh updates all components simultaneously

## Deliverables

### Single Unified Section
- ✅ All Dashboard-related tasks consolidated into [COMPONENT_DASHBOARD] section
- ✅ Tasks grouped logically by component and functionality
- ✅ Component tags reference established legend ([TAS], [AS], [DNC], [CBC], [TT], [AT])

### Deduplication Verification
- ✅ Every Dashboard item from source files appears exactly once
- ✅ No duplicate tasks between components
- ✅ Cross-references maintained where tasks affect multiple components
- ✅ Source file mapping preserved in task descriptions

### Actionable Task Structure
- ✅ All tasks written as actionable checkbox items
- ✅ Acceptance criteria defined for measurable outcomes
- ✅ Component relationships clearly documented
- ✅ Priority indicated through logical grouping and ordering
