# ✅ FEATURE AUDIT: RECURRING TRANSACTIONS (2025-05-06)

## 📦 Backend Model Summary

```py
class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(64), db.ForeignKey("transactions.transaction_id"), nullable=False)
    transaction = db.relationship("Transaction", backref="recurrence_rule")

    frequency = db.Column(db.String(64), nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=timezone.utc), onupdate=lambda: datetime.now(tz=timezone.utc))
    next_instance_id = db.Column(db.String(64), nullable=True)
```

## 🧠 Key Observations

- Backend model and routes **support full lifecycle**: create, update, fetch, and delete recurring transactions.
- Frontend has **functional base components** for recurring management: manual rule entry, edit, delete, and display.
- Merging of auto + user reminders works in `/recurring` GET route.
- Recurring rule creation leverages `/recurringTx` PUT and will soon include `/rules/new` POST.
- **No current support** for _recurring rule templates_, _bulk patterns_, or _frequency intelligence_.
- Transaction table now supports inline editing of key fields and prompts for rule creation.

## 📝 Updated Checklist

### ✅ Core Functionality

- [x] Save recurring rule via `tx_id` or `account_id`
- [x] Edit existing rules
- [x] Delete user-defined rules
- [x] Merge user + auto-detected reminders in backend
- [x] Create rule from edited transaction with confirmation

### 🚧 Frontend Enhancements

- [x] Inline editing of transactions table
- [x] Inline save feedback via toast messages
- [x] Prompt rule creation on matching edit
- [ ] Validate recurring edits (amount, date, category)
- [ ] Modal or toast-confirmation for "always apply this rule"
- [ ] Highlight if a rule already exists for a given condition

### 📬 Notifications / Feedback

- [x] Toast notification on transaction update success
- [x] Toast error on failure
- [x] Toast feedback for rule creation or skip

### 🧭 Future Features

- [ ] Simulate upcoming instances (next 3 months)
- [ ] Detect recurrence patterns from transaction history
- [ ] Merge similar entries into 1 rule
- [ ] Graph of future recurring cashflow

---

_Last synced: 2025-05-06_
