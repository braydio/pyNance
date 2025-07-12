# 📘 `User` Model

```markdown
# User Model

## Purpose

Represents an authenticated user in the system. Each user is the owner of a full financial workspace including accounts, transactions, categories, and settings.

## Fields

- `id`: Primary key (UUID or integer)
- `email`: Login email, unique
- `name`: Full name or display name
- `password_hash`: Encrypted login credential
- `created_at`, `updated_at`: Audit timestamps
- `timezone`: Optional — user-local TZ for reports
- `is_active`: Boolean flag for account status
- `onboarding_status`: Enum or string tracking profile setup steps

## Relationships

- One-to-many with `Account`, `Transaction`, `RecurringTransaction`, `Category`
- Links to session store and auth tokens

## Behaviors

- Used as top-level filter in most queries
- Soft deletion disables access but preserves data
- On creation, triggers default category and setting seeding

## Related Logic

- Auth, token management, and user-scoped filters
 - `account_logic.py`
- Admin tools for impersonation or override

## Related Docs

- [`docs/auth/user_authentication.md`](../../docs/auth/user_authentication.md)
- [`docs/frontend/pages/UserSettings.md`](../../docs/frontend/pages/UserSettings.md)
```
