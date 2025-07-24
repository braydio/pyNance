# Dashboard Development To-Do (Codex)

This document tracks outstanding items for finalizing `Dashboard.vue` and related layout components. Follow these notes when polishing the dashboard experience.

## 1. Spending Insights Panel
- Replace the placeholder panel with meaningful insights or charts once designs are available.
- Tie data into existing analytics helpers.

## 2. Category Spending Chart UX
- Keep the chart wide enough and visually balanced at all breakpoints.
- Review date pickers and dropdown menus for mobile and desktop usability.
- Ensure all inputs have accessible labels.

## 3. Accounts & Transactions Tables
- Expand/collapse works, but micro‑interactions could be smoother.
- Consider sticky headers or pagination for users with many records.
- Provide test or fake data for empty states.

## 4. Responsiveness Review
- Perform a final responsive audit across devices.
- Restyle the Navbar (`frontend/src/components/layout/Navbar.vue`) so it fits the dashboard layout.

## 5. Accessibility Review
- Validate tab order, aria labels, and color contrast.
- Confirm keyboard navigation works in tables and filters.

## 6. Minor Polish
- Double-check spacing, shadows, icon sizes, and text wrapping.
- Optional: add unit or Cypress tests for expand/collapse and snapshot accuracy.
- Optional: add animations for table transitions or modal dialogs.
