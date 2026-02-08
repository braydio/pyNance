## Transactions performance playbook

- **Backend caching:** `/api/transactions/get_transactions` and `/api/transactions/<id>/transactions` cache pages 1–5 for 90 seconds per filter set. Keys include page, page_size, date range, account filters, and tx_type. Cache is auto-busted whenever transactions are upserted or refreshed.
- **Prefetch on the client:** The transactions composable prefetches the next two pages after the current one (up to page 3) and serves them instantly from a page cache keyed by the active filters. Filter changes reset the cache.
- **Metadata:** The API now returns a `meta` object with paging info and a `cache_hit` flag so UI and ops can see when responses are served from cache.
- **Balance history:** Balance history is derived server-side and cached in `account_history`; use `/api/accounts/<account_id>/history` for precomputed series when you need historical balances.
- **Staleness & rate limits:** Refresh endpoints expose `refresh_status` and `refresh_status` can be read via `/api/accounts/refresh_status` to show stale/rate-limited accounts in the UI.

### Fast-path fetch recipe (UI)

1. Request page 1 immediately; show skeleton rows.
2. Prefetch pages 2–3 in the background (only if not cached).
3. Use the cached pages for pagination; only hit the API when a page is missing or stale.
4. Optionally fetch balance history in parallel for charts; don’t block the table render.

### Timing instrumentation (planned)

- Add lightweight DEBUG-level timers around each chart endpoint to log execution duration (e.g., `category_breakdown`, `cash_flow`, `net_assets`). This stays out of INFO to avoid noise and helps pinpoint slow queries during dashboard loads.
