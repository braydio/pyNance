## 📘 `cron_balance_history.py`
```markdown
# Cron Balance History Script

Standalone entry point intended to be run on a schedule (e.g., via cron). It
refreshes cached `account_history` records for all accounts so balance
history consumers can render without gaps.

Example crontab (hourly):
0 * * * * cd /path/to/pyNance && /usr/bin/env python backend/cron_balance_history.py >> logs/cron_balance_history.log 2>&1
```
