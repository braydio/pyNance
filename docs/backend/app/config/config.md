# 📘 `config/` Module Documentation

```markdown
# config/ Directory

## Purpose

Houses all configuration logic used during application initialization. Includes environment-based settings, constants, and framework integrations. Centralizes control of runtime behavior for development, testing, and production environments.

## Files

- `__init__.py`

  - Marks this directory as a Python package

- `settings.py`

  - Main configuration loader
  - Reads from environment variables, `.env`, or config secrets
  - Defines:
    - `DATABASE_URL`
    - `PLAID_CLIENT_ID`, `PLAID_SECRET`
    - `TELLER_TOKEN`, `JWT_SECRET`, `DEBUG`
    - Feature toggles, environment flags, Sentry keys

- `env.py`
  - Utility loader for `.env` parsing and variable substitution
  - May wrap `os.environ`, `dotenv`, or `pydantic` config

## Common Patterns

- `.getenv("FOO", fallback)` usage with type coercion
- Structured config classes (e.g., `class AppConfig`) with typed fields
- Environment isolation via `APP_ENV = dev|prod|test`

## Usage

- Imported by:
  - `main.py` to load Flask/FastAPI config
  - `services/` and `sql/` to get DB connection strings
  - CLI scripts to dynamically adjust logging or sync limits

## Related Docs

- [`docs/dev/environment.md`](../../docs/dev/environment.md)
- [`docs/infra/deployment.md`](../../docs/infra/deployment.md)
```

---

Would you like to continue with `cli/` next or explore `utils/`?
