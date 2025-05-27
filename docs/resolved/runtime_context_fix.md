# Resolved: RuntimeError - Working outside of application context

** – Date
2025-05-24

** 🏉 Root Cause
A `db.session.commit()` call was accidentally left at module-level scope in `account_logic.py`, causing SQLAlchemy to run without an active Flask app context when Flask tried to import the module during startup.

** 🐘 Fix
Moved the `db.session.commit()` back **inside** the `upsert_accounts()` function.

This ensures it only runs in a registered app context, not on import.
```\ndef upsert_accounts(...):
    ...\n    db.session.commit()
    logger.info("Finished upsert")
```

** <é Error Message
```
RuntimeError: Working outside of application context.
```

** – Confirmed Resolved
- Server now starts cleany with both `flask run` and `python run.py`
- Full runtime context restored

---
This file is kept for reference in case similar issues arise with app context-dependent logic during import time.
