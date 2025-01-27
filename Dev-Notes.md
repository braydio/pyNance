We can update this file with development notes - process improvement idease - new functionalities ideas etc. Copying in the latest dev notes from the README. Also see the guide for the dev-tools below.
    - I moved the guide for the dev-tools to Dev-Tools-Guide.md

### Current Development State (1/26)
- Plaid Link is fully integrated. SQL Server initialized. 
    - I'm using DB Browser for SQL DB Mgmt
    - Currently all API responses are saved as JSON files in Dash/data where they are loaded by the handlers.
        - See the MainDash.py backend for the account refresh and account link logic - it's easier to follow IMO.
    - TO-DO includes finish polished the Account Refresh logic, passing the data correctly to the DB.
        - Not sure if we want to use SQL and ditch the JSON logic, or use JSON for the recent activity and SQL for older transactions.

We could probably work on a more robust workflow. I'll make a second markdown file with version notes / working notes.

Okay I made it. It's Called Dev-Notes.md.

Oh good, you found it.

# Latest - Brayden - Processing API Response for Transactions

### Process Transactions Function

## Overview
The `process_transactions` function processes transaction data from the temporary file (`TRANSACTION_REFRESH_FILE`), enriches it with account and item details, and saves the enriched data to the permanent file (`LATEST_TRANSACTIONS`).

## Workflow
1. **File Loading**:
   - Reads raw transaction data from `TRANSACTION_REFRESH_FILE`.
   - Loads `LINKED_ACCOUNTS` and `LINKED_ITEMS` for enriching transactions.

2. **Data Enrichment**:
   - Adds the following details to each transaction:
     - `institution_name`
     - `account_name`
     - `account_type`
     - `account_subtype`
     - `last_successful_update`

3. **Data Saving**:
   - Saves enriched transactions to `LATEST_TRANSACTIONS` in JSON format.

4. **Error Handling**:
   - Handles missing files, invalid JSON formats, and unexpected errors with detailed logs and meaningful API responses.

## API Endpoint
- **Route**: `/process_transactions`
- **Method**: `POST`
- **Response**:
  - Success: 
    ```json
    { "status": "success", "message": "Transactions processed successfully." }
    ```
  - Errors: Returns appropriate error messages for missing files or invalid JSON.

## Example Usage
1. Trigger the function via a POST request after fetching/refreshing transactions.
2. The enriched data is saved to `LATEST_TRANSACTIONS` for rendering on the transactions page or further processing.

## Notes
- Ensure the `TRANSACTION_REFRESH_FILE` is updated with the latest raw transactions before calling this endpoint.
- This function is designed to streamline transaction enrichment and storage.
