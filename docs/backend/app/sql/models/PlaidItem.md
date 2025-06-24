# 📘 `PlaidItem` Model
```markdown
# PlaidItem Model

Stores Plaid item metadata for each user and product. Used to persist
access tokens returned by Plaid and reference the associated institution
name and product type.

## Fields
- `id`: Primary key
- `user_id`: ID of the owning user
- `item_id`: Plaid item identifier (unique)
- `access_token`: Access token for API calls
- `institution_name`: Name of the linked institution
- `product`: Plaid product this item grants access to
- `is_active`: Soft delete flag
- `created_at`, `updated_at`: Audit timestamps
```
