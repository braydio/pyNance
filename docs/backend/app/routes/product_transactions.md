---

## 📘 `product_transactions.py`

```markdown
# Product Transactions Route

## Purpose
Handles ingestion and display of transactions tied to specific products or merchant items. This supports granular expense tracking and product-level budgeting.

## Key Endpoints
- `GET /products/transactions`: Fetch transactions annotated with product-level metadata.
- `GET /products/summary`: Aggregated spending per product category or SKU.

## Inputs & Outputs
- **GET /products/transactions**
  - **Params:** `category_id`, `merchant_id`, `date_range`
  - **Output:**
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

- **GET /products/summary**
  - **Output:**
    ```json
    {
      "categories": [
        { "name": "Tech", "total_spent": 843.19 },
        { "name": "Groceries", "total_spent": 214.75 }
      ]
    }
    ```

## Internal Dependencies
- `services.product_transaction_parser`
- `models.Transaction`
- `utils.product_classifier`

## Known Behaviors
- May use embedded merchant metadata for classification
- Enables per-item budgeting and tagging
- Relies on enriched transaction data from imports or manual tagging

## Related Docs
- [`docs/dataflow/product_categorization.md`](../../dataflow/product_categorization.md)
- [`docs/models/ProductTransaction.md`](../../models/ProductTransaction.md)
```

---

Next: `recurring.py`?
