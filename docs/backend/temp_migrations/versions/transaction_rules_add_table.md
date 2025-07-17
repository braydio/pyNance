## 📘 `add_transaction_rules_table.py`
```markdown
# Migration: Add Transaction Rules Table

This migration creates the `transaction_rules` table used for automatic transaction updates.

1. **Generate the migration**

```bash
flask db migrate -m "add transaction rules table"
```

The command produces `backend/migrations/versions/<revision>_add_transaction_rules_table.py`.

2. **Define the table**

Edit the new file so `upgrade()` contains:

```python
op.create_table(
    "transaction_rules",
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("user_id", sa.String(64), index=True),
    sa.Column("match_criteria", sa.JSON(), nullable=False),
    sa.Column("action", sa.JSON(), nullable=False),
    sa.Column("is_active", sa.Boolean(), default=True),
    sa.Column("created_at", sa.DateTime(), nullable=False),
    sa.Column("updated_at", sa.DateTime(), nullable=False),
)
```

Include a matching `downgrade()` that drops the table.

3. **Apply the migration**

```bash
flask db upgrade
```

4. **Validate**

Check the database schema to ensure `transaction_rules` exists before enabling the feature.
```
