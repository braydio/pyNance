# Recurring Transactions: Feature Specification & Architecture

## 1. Overview

Recurring transactions allow users to define rules for transactions that repeat over time (e.g., rent, subscriptions). These rules are used to simulate future financial activity, detect expected patterns, and enhance forecasting accuracy.

---

## 2. Core Functional Requirements

### 2.1 Rule Structure

Each rule must include:

- Linked `tx_id` or `account_id`
- Frequency (e.g., weekly, monthly, custom date set)
- Description, category, merchant (optional overrides)
- Next occurrence date
- Active status flag

### 2.2 Actions Supported

- Save new rule
- Edit existing rule
- Delete rule
- Merge overlapping rules (user-defined + auto-detected)

### 2.3 Validation Rules

- Required: `frequency`, `next_date`
- Optional: `merchant`, `description`, `category`
- Validate date is not in the past unless marked as `historical`

---

## 3. Backend Integration

### 3.1 Data Model

A rule object stored in the database should include:

- `rule_id`, `tx_id`, `account_id`
- `frequency` (ISO or enum format)
- `start_date`, `last_occurred`, `next_due`
- Optional fields: `notes`, `category_override`, `is_active`

### 3.2 API Endpoints

- `POST /api/recurring/save`
- `PUT /api/recurring/update`
- `DELETE /api/recurring/:id`
- `GET /api/recurring/simulate`

### 3.3 Business Logic

- Merge rules by common merchant or category pattern
- Detect and warn about missed occurrences (based on last_occurred)
- Allow silent simulation (no DB write) for preview

---

## 4. Development Roadmap Checklist

### ❌ Core Functionality

- [x] Save recurring rule via `tx_id` or `account_id`
- [x] Edit existing rules via dedicated recurring form
- [x] Delete user-defined rules
- [x] Merge user + auto-detected reminders in backend

### 🍍 😅 III Improvements

- [ ] 🔏 Fix broken Edit button in `UpdateTransactionsTable.vue`
- [ ] Add inline editing for recurring rules in table
- [ ] Add toast notifications (success, error) for save/delete/import
- [ ] Add validation to recurring form (required fields, invalid dates)
- [ ] Add confirmation UI after saving or editing a rule

### 💉 Smart Recurrence Logic

- [ ] Frequency inference from transaction patterns
- [ ] Simulation UI: preview upcoming instances (e.g., next 3 months)
- [ ] Smart merging of similar rules (e.g., Spotify/Spotify Ltd.)
- [ ] Visual indicators for near-due reminders

### 📀 Backend Enhancements

- [x] Support resolving `account_id` via `tx_id` on save
- [ ] Add endpoint for rule simulation preview
- [ ] Detect out-of-sync recurring rules (e.g., missed dates)

### 🖓 Usability Enhancements

- [ ] Add loading state on save/delete
- [ ] Reset form after success, focus user feedback
- [ ] Support multiple account selection scenarios (power users)

---

_Last updated: 2025-05-09_
