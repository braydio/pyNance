---
# 📚 Recurring Transactions System Reference (pyNance Dashroad)

This document outlines how recurring transactions are **identified**, **stored**, **updated**, and **served** within the pyNance application.
---

## ⚙️ Core Concepts

### 🔁 What is a Recurring Transaction?

A recurring transaction is a known repeating financial activity (e.g. rent, salary) tracked either:

- **Automatically**, via heuristics
- **Manually**, by user definition

---

## 🧱 Database Model

### `RecurringTransaction` (SQLAlchemy Model)

Stored in the backend's `models.py`:

- `account_id`: linked to user account
- `description`: summary label
- `amount`: expected amount
- `frequency`: one of `daily`, `weekly`, `monthly`, `yearly`
- `next_due_date`: next expected payment date
- `notes`: optional
- Supports creation and update timestamps

---

## 🌐 Backend API Endpoints

Defined in: `backend/app/routes/recurring.py`

---

### ### 1. **POST** `/api/<account_id>/recurringTx`

#### 🔹 Purpose:

Create or update a manual recurring transaction.

#### 🔹 Request Body:

```json
{
  "description": "Rent",
  "amount": 1200.0,
  "frequency": "monthly",
  "notes": "Paid to landlord",
  "next_due_date": "2025-06-01"
}
```

#### 🔹 Behavior:

- If `description` and `amount` match existing record → update
- Else → insert new recurring record
- If `next_due_date` is invalid, fallback to 30 days from today

#### 🔹 Returns:

```json
{ "status": "success", "message": "Recurring transaction saved." }
```

---

### 2. **GET** `/api/<account_id>/recurring`

#### 🔹 Purpose:

Return all **reminders** from:

- Auto-detected recurring patterns
- User-defined recurring entries

#### 🔹 Logic:

- Query last 90 days of transactions by description + amount
- Identify clusters (≥2 matches) → treat as recurring
- Calculate **next due date**
- Compare to `today` → if due within 7 days, return as a reminder

#### 🔹 Sample Return:

```json
{
  "status": "success",
  "reminders": [
    "Reminder (Auto): Rent ($1200) due on Jun 1",
    "Reminder (User): Spotify ($9.99) is due on Jun 3"
  ]
}
```

---

## 🔎 Frontend Integration

### `RecurringTransactionSection.vue`

- Used in `Transactions.vue`
- UI Form Inputs:

  - `Transaction ID`
  - `Description`, `Amount`
  - `Frequency`, `Next Due Date`, `Notes`

- Saves entry using:

  ```js
  await createRecurringTransaction(txId, { ...fields })
  ```

---

## 📥 File Upload Support

- Not directly tied to recurring system
- Imported transactions **can trigger auto-detection**

---

## 🧠 Helper Function: `add_months(date, months)`

- Adds `X` months to a given `date`
- Handles month/year rollovers (e.g. Dec + 1 = Jan next year)

---

## ✅ Summary

| Area            | Description                                 |
| --------------- | ------------------------------------------- |
| 📘 Storage      | `RecurringTransaction` model                |
| 🛠 Manual Entry | `/recurringTx` POST                         |
| 🧠 Detection    | Clustered similarity (amount + description) |
| 🔔 Reminders    | If next due is within 7 days                |
| 📦 Output       | `reminders[]` string array                  |
| 📱 UI Link      | `RecurringTransactionSection.vue`           |

---
