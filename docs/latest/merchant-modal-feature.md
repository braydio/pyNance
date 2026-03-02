---
Owner: Brayden
Last Updated: 2026-03-01
Status: Implemented
---

# Merchant Bar Click → Transaction Modal

## Overview

Enable users to click on a merchant bar in the Category Breakdown chart (Merchant view) to open a modal showing all transactions for that merchant within the selected date range.

## Problem

Users viewing spending by merchant wanted to drill down into specific merchants to see individual transactions, but this functionality was blocked in the code.

## Solution

Added backend API support for filtering transactions by merchant, and wired up the frontend to handle merchant bar clicks.

## Files Modified

### Backend

| File | Change |
|------|--------|
| `backend/app/sql/account_logic.py` | Added `merchant` parameter to `get_paginated_transactions()` with filter using `merchant_slug` OR `merchant_name` |
| `backend/app/routes/transactions.py` | Added `merchant` query parameter to `/api/transactions/get_transactions` endpoint |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/api/transactions.js` | Added `merchant` param handling in `fetchTransactions()` |
| `frontend/src/views/Dashboard.vue` | Removed block on merchant clicks, added `onMerchantBarClick()` handler |
| `frontend/src/components/modals/TransactionModal.vue` | Added `subtitlePrefix` prop for dynamic "Merchant" label |

## API Contract

### Request

```
GET /api/transactions/get_transactions?merchant=<merchant_name_or_slug>&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `merchant` | string | Filter by merchant name or merchant slug |
| `start_date` | string | Start date (YYYY-MM-DD) |
| `end_date` | string | End date (YYYY-MM-DD) |

### Response

Standard paginated transactions response with transactions filtered by merchant.

## Architecture Decision

### Why filter by both `merchant_slug` AND `merchant_name`?

```python
query.filter(
    (Transaction.merchant_slug == merchant) | 
    (Transaction.merchant_name == merchant)
)
```

- `merchant_slug` is indexed in the database (faster lookups)
- `merchant_name` provides fallback for cases where slug isn't set
- This ensures users can click on any merchant name displayed in the chart

## User Flow

1. User navigates to Dashboard
2. User switches Category Breakdown to "Merchant" view
3. User sees bars for each merchant with total spend
4. User clicks on a merchant bar
5. Modal opens showing all transactions for that merchant in the selected date range
6. Modal header shows "Merchant: [Merchant Name]"

## Testing

### Manual Test

1. Start backend and frontend servers
2. Go to Dashboard
3. Locate Category Breakdown section
4. Switch dropdown to "Merchant" view
5. Click on any merchant bar
6. Verify modal opens with transactions filtered for that merchant

### API Test

```bash
curl "http://localhost:5000/api/transactions/get_transactions?merchant=STARBUCKS&start_date=2026-01-01&end_date=2026-01-31"
```

## Future Improvements

- [ ] Add database index on `merchant_name` for improved query performance
- [ ] Support filtering by multiple merchants simultaneously
- [ ] Add merchant search/filter in modal header
- [ ] Consider caching merchant transaction results

## Related Documentation

- [Dashboard Component Spec](../frontend/dashboard-component-spec.md)
- [Transaction Modal Guide](../frontend/DASHBOARD_MODAL_GUIDE.md)
- [Transactions API Reference](../backend/api-reference.md)
