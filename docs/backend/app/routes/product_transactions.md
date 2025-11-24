# Product Transactions Route (`product_transactions.py`)

## Purpose
Handle ingestion and display of transactions tied to specific products or merchant items for granular expense tracking and budgeting.

## Endpoints
- `GET /products/transactions` – Fetch transactions annotated with product-level metadata.
- `GET /products/summary` – Retrieve aggregated spending per product category or SKU.

## Inputs/Outputs
- **GET /products/transactions**
  - **Inputs:** Optional `category_id`, `merchant_id`, and `date_range` filters.
  - **Outputs:** Array of enriched transactions including product names, amounts, merchants, and dates.
- **GET /products/summary**
  - **Inputs:** Optional filters aligned with transaction query params.
  - **Outputs:** Aggregated totals per product/category (e.g., `{ "categories": [{ "name": "Tech", "total_spent": 843.19 }] }`).

## Auth
- Requires authenticated user; results are scoped to the user's transactions.

## Dependencies
- `services.product_transaction_parser` for enrichment.
- `models.Transaction` and product classification utilities.

## Behaviors/Edge Cases
- Leverages merchant metadata for classification; relies on enriched data from imports or manual tagging.
- Supports per-item budgeting and tagging workflows.

## Sample Request/Response
```http
GET /products/transactions?merchant_id=amazon HTTP/1.1
```

```json
[
  {
    "transaction_id": "txn_202",
    "product_name": "Kindle Paperwhite",
    "amount": 129.99,
    "merchant": "Amazon",
    "date": "2024-11-10"
  }
]
```
