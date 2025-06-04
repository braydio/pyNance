# 🧱 Dashboard Mock Layout Plan

**Date:** {datetime.utcnow().isoformat()}  
**Purpose:** Plan and break down development for `DashboardMock.vue` — a feature-rich mock dashboard view.

---

## 🔧 Overview

This document defines **six key action items** that represent the functional and visual layout of a new Vue component for the dashboard. This roadmap will be implemented in the `frontend/src/views/DashboardMock.vue` file and is meant to simulate real dashboard interactivity using mocked data.

---

## ✅ Action Item 1: TopBar Header

**Goal:** Build a responsive and feature-rich top navigation bar.

**Features to include:**

- 📅 **Date Range Picker** (mock calendar dropdown, last 30 days by default)
- 👤 **User Section** with avatar and name (`"Brayden"` for mock purposes)
- 🔔 **Notification Icon** with red badge for unread alerts (e.g., `3`)
- ⚙️ **Settings Dropdown** (stub only, no action required)
- 🌗 **Dark/Light Mode Toggle** that reflects theme in mock
- 📱 Fully responsive: stack vertically on narrow screens

---

## ✅ Action Item 2: Net Worth Overview Widget

**Goal:** Present a clean, eye-catching summary of net worth.

**Details:**

- Show **Total Net Worth**: e.g., `$12,340.00`
- Indicator: **Gain/Loss Since Last Period** with arrow and delta
- 🟢 Positive = green arrow up, 🔴 Negative = red arrow down
- Positioned in a top-level row with optional background gradient
- Tooltip: “Calculated as total assets minus liabilities”

---

## ✅ Action Item 3: Daily Net Income Chart + Modal

**Goal:** Visualize daily net income, and show details on click.

**Functionality:**

- 📊 Horizontal bar chart for past 30 days
- Bars represent `income - expenses` per day
- OnClick:
  - Opens **modal table** with:
    - Category
    - Amount
    - Description
    - Type (income/expense)
  - Clicking the same bar again **closes** the modal
- Modal should be reusable (`<TransactionModal />`)
- Smooth animation for modal entry/exit

---

## ✅ Action Item 4: Upcoming Bills Tracker

**Goal:** Display upcoming recurring transactions in a scannable list.

**Details:**

- Vertical or horizontal scrollable card list
- Each item:
  - 🧾 Bill name
  - 💵 Amount
  - 📅 Due date (formatted `MMM DD`)
  - ⚠️ Highlight:
    - Yellow = due in ≤ 3 days
    - Red = overdue
- UI is passive: no interaction required yet

---

## ✅ Action Item 5: Hide/Show Accounts Toggle

**Goal:** Let user hide specific accounts from dashboard views.

**Features:**

- Sidebar list or dropdown showing all connected accounts (mocked)
- Each account has:
  - Eye/eye-slash toggle icon
  - Name, balance
- Toggling:
  - Updates local state
  - Affects what’s shown in widgets & charts
- Optional: counter for “hidden” accounts + “show all” button

---

## ✅ Action Item 6: File & Component Structure

**Goal:** Organize reusable components and code.

**Structure:**

- `frontend/src/views/DashboardMock.vue`: Primary file
- Components created/reused from:
  - `components/widgets/NetWorthCard.vue`
  - `components/charts/DailyNetChart.vue`
  - `components/modals/TransactionModal.vue`
- Composition API using `<script setup>`, `ref`, and `computed`
- Minimal CSS-in-Vue; prefer utility classes or scoped

---

## 🔁 Next Steps

Once confirmed, proceed to implement **Action Item 1**.  
Each section will be coded and validated before progressing.

---

"""

doc_path.write_text(markdown_content)
doc_path.name
