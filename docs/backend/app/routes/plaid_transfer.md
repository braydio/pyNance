# Plaid Transfer Route (`plaid_transfer.py`)

## Purpose
Enable money movement through Plaid-linked bank accounts, covering initiation, status lookups, and history retrieval.

## Endpoints
- `POST /plaid/transfer/initiate` – Start a new bank transfer.
- `GET /plaid/transfer/status/<transfer_id>` – Fetch status for a specific transfer.
- `GET /plaid/transfer/history` – List past transfer attempts.

## Inputs/Outputs
- **POST /plaid/transfer/initiate**
  - **Inputs:** `{ "amount": float, "destination_account_id": str, "description": str }`.
  - **Outputs:** `{ "transfer_id": "trf_123", "status": "pending" }` after submission.
- **GET /plaid/transfer/status/<transfer_id>**
  - **Inputs:** Path parameter `transfer_id`.
  - **Outputs:** Status payload such as `{ "status": "completed", "settled_at": "2024-11-20T10:30:00Z" }`.
- **GET /plaid/transfer/history**
  - **Inputs:** None.
  - **Outputs:** Array of transfer metadata for the authenticated user.

## Auth
- Requires authenticated user; transfers are validated against the user's eligible Plaid accounts.

## Dependencies
- `services.transfer_service` orchestrating Plaid Transfer client interactions.
- `models.Transfer` and Plaid SDK components for persistence and execution.

## Behaviors/Edge Cases
- Uses idempotent submission to prevent duplicate transfers.
- Surfaces eligibility errors when accounts cannot support transfers.

## Sample Request/Response
```http
POST /plaid/transfer/initiate HTTP/1.1
Content-Type: application/json

{ "amount": 150.0, "destination_account_id": "plaid_002", "description": "Rent payment" }
```

```json
{ "transfer_id": "trf_123", "status": "pending" }
```
