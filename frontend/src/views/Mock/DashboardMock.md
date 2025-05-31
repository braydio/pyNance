# Directory for design of Dashboard.vue
# 📊 DashboardMock.vue Layout Plan

**Purpose:**
Define and scope a Vue-based dashboard mock for `DashboardMock.vue` under `frontend/src/views`. This file outlines 6 key feature areas to build a functional, insight-driven dashboard interface for financial tracking.

---

## 1. ✨ Top Bar Navigation (Global Controls)

**Purpose:** Provide app-wide context, branding, and core controls.

**Contents:**

* **App Title/Logo**: Positioned top-left.
* **User Display**: Show current user or "Welcome Back, \[Name]" message.
* **Date Range Selector**: Default to current month. Use dropdown or calendar picker.
* **Global Filter/Settings Button**: Access to preferences, theme toggle, or hidden account settings.
* **Account Toggle Visibility**: Button or dropdown to show/hide specific accounts from dashboard views.

**Special Requirements:**

* State persists across route changes (Vuex or Pinia).
* Animations for hiding/showing accounts.

---

## 2. 💸 Daily Net Income Bar Chart

**Purpose:** Show net income (income - expenses) for each day in the selected date range.

**Contents:**

* **X-axis**: Dates.
* **Y-axis**: Net income (positive or negative).
* **Bar**: Color-coded bars for each day.
* **Hover Tooltip**: Show value, date.
* **Click Interaction**: Opens transaction detail modal for that day.

**Data Format:**

```ts
interface NetIncomeByDay {
  date: string; // YYYY-MM-DD
  income: number;
  expenses: number;
  net: number;
}
```

---

## 3. ❌ Skipped Item (Previous Number 3)

> Not required at this time.

---

## 4. ❌ Skipped Item (Previous Number 4)

> Not required at this time.

---

## 5. 📆 Transaction Modal Table (Click Bar to Open)

**Purpose:** Display transactions for a specific day in detail.

**Triggered By:** Clicking any bar in the net income chart.

**Contents:**

* **Header**: Date selected.
* **Table Columns**: Description, Amount, Category, Type, Time.
* **Pagination (if needed)**
* **Close Button**: To dismiss modal.
* **Transaction Highlights**: Bold negative amounts.

**Expected Data:**

```ts
interface Transaction {
  id: string;
  date: string;
  amount: number;
  description: string;
  category: string;
  type: 'income' | 'expense';
  time: string;
}
```

**UX Detail:**

* Animate open/close.
* Re-click same bar = toggle close.

---

## 6. ❌ Skipped Item (Previous Number 6)

> This feature has been intentionally deferred.

---

Let me know if you'd like to revise or reorder any items.

---

**Next Step:** Begin implementation of Action Item **1: Top Bar Navigation**.
