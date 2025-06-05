## 📘 `cron_sync.py`
```markdown
# Cron Sync Script

Standalone entry point intended to be run on a schedule (e.g., via cron). It
configures logging to `cron.log` and calls
`account_refresh_dispatcher.refresh_all_accounts()` to keep account data up to
date.
```
