# 🕦 Recurring Transactions – Development Roadmap (Updated)

### ✅ Core Functionality

- [x] Save recurring rule via `tx_id` or `account_id`
- [x] Edit existing rules via dedicated recurring form
- [x] Delete user-defined rules
- [x] Merge user + auto-detected reminders in backend

### 🧩 Frontend Enhancements

- [ ] 🔧 Fix broken Edit button in `UpdateTransactionsTable.vue`
- [ ] Add inline editing for recurring rules in table
- [ ] Add toast notifications (success, error) for save/delete/import
- [ ] Add validation to recurring form (required fields, invalid dates)
- [ ] Add confirmation UI after saving or editing a rule
- [ ] Improve formatting for upcoming reminders (e.g., highlight near-due)
- [ ] Frequency presets or smart suggestions

### 🧠 Smart Recurrence Logic

- [ ] Frequency inference from transaction patterns
- [ ] Simulation UI: preview upcoming instances (e.g., next 3 months)
- [ ] Merge similar recurring entries into a unified rule
- [ ] Visual indicators for near-due or overdue rules
- [ ] Graph of predicted recurring impact over time

### 🧪 Backend Enhancements

- [x] Support resolving `account_id` via `tx_id` on save
- [ ] Add backend endpoint for recurring rule simulation preview
- [ ] Detect and flag out-of-sync recurring rules

### 🛠 Usability Enhancements

- [ ] Add loading state during save/delete operations
- [ ] Reset and clear form after success
- [ ] Support account selection in multi-account mode

---

_Last updated: 2025-05-06_
