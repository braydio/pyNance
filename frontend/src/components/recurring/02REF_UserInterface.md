# Recurring Transactions: UI/UX Guide

## 1. Interface Goals

Ensure recurring rules can be managed smoothly within the transaction editing workflow and simulated for future forecasting, while providing immediate user feedback and maintaining visual clarity.

---

## 2. UI Components & Behaviors

### 2.1 UpdateTransactionsTable Enhancements

- Inline icon (⟳) or label for recurring transactions
- Edit button triggers rule form modal or row inline edit
- Visual tag: e.g., `Recurring`, `Upcoming`, `Missed`

### 2.2 Recurring Rule Form

- Fields: Frequency, Next Date, Optional Description, Category
- Validations: required frequency/date, disallow past unless historical
- Save, Cancel, Delete buttons with full feedback

### 2.3 Toast Notifications

- Display on Save, Edit, Delete actions
- Position: top-right corner
- Types:

  - ✅ Success: “Rule saved”
  - ❌ Error: “Invalid input” / “Server error”
  - ⚠️ Info: “Simulated rule not saved”

---

## 3. Simulation UI

### 3.1 Preview Panel

- Display up to next 3 simulated occurrences
- Highlight calendar pattern or expected gaps
- Option to convert preview to active rule

### 3.2 Smart Merge Suggestions

- Suggest combining similar merchant names
- Example: `Spotify Ltd.` + `Spotify` → Unified recurring rule

---

## 4. Visual Indicators

| Indicator | Meaning             | Location         |
| --------- | ------------------- | ---------------- |
| ⟳ Label   | Active recurring tx | Transaction row  |
| 🟡 Tag    | Upcoming occurrence | Simulation panel |
| 🔴 Alert  | Missed occurrence   | Rule editor row  |

Color and icon standards should remain consistent with other dashboard alerts.

---

## 5. Accessibility & UX Enhancements

- Tab-navigable recurring form
- Auto-reset form after save
- Focus returns to previous row/button
- Mobile: collapse inline rule form into modal
- Responsive indicators and button spacing

---

_Last updated: 2025-05-09_
