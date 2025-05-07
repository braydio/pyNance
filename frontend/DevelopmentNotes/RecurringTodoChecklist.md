# 🕦 Recurring Transactions – Development Roadmap (Updated)

### ✗ Core Functionality
- [x] Save recurring rule via `tx_id` or `account_id`
- [x] Edit existing rules via dedicated recurring form
- [x] Delete user-defined rules
- [x] Merge user + auto-detected reminders in backend

### � 😅 III Improvements
- [ ] 🔟 Fix broken Edit button in `UpdateTransactionsTable.vue`
- [ ] Add inline editing for recurring rules in table
- [ ] Add toast notifications (success, error) for save/delete/import
- [ ] Add validation to recurring form (required fields, invalid dates)
- [ ] Add confirmation UI after saving or editing a rule

### 🐉 Smart Recurrence Logic
- [ ] Frequency inference from transaction patterns
- [ ] Simulation UI: preview upcoming instances (e.g., next 3 months)
- [ ] Smart merging of similar rules (e.g., Spotify/Spotify Ltd.)
- [ ] Visual indicators for near-due reminders

### 📰 Backend Enhancements
- [x] Support resolving `account_id` via `tx_id` on save
- [ ] Add endpoint for rule simulation preview
- [ ] Detect out-of-sync recurring rules (e.g., missed dates)

### 🖓 Usability Enhancements
- [ ] Add loading state on save/delete
- [ ] Reset form after success, focus user feedback
- [ ] Support multiple account selection scenarios (power users)

---
_Last updated: 2025-05-06_