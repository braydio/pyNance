# Dashboard Greeting Status

## Overview

The main dashboard greeting now uses a backend-generated status message instead of a static net-worth quip. The status is designed to be parseable and display one practical suggestion to help the user act on recent activity.

## API contract

- Frontend request: `GET /api/dashboard/activity-status`
- Optional query params: `start_date`, `end_date`, `user_id`
- Expected success shape:

```json
{
  "status": "success",
  "data": {
    "status_key": "largest_expense",
    "message": "Review your largest recent expense for accuracy.",
    "source": "llm"
  }
}
```

## Frontend behavior

- `Dashboard.vue` fetches activity status alongside other initial dashboard requests.
- `NetOverviewSection.vue` displays the `message` in the greeting block.
- If the request fails, existing dashboard fallback messaging remains in place.
