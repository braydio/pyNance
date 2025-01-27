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

# Process Transactions Function

## Overview
The `process_transactions` function processes transaction data from the temporary file (`TRANSACTION_REFRESH_FILE`), enriches it with account and item details, and saves the enriched data to the permanent file (`LATEST_TRANSACTIONS`). It includes a 24-hour cooldown to prevent frequent refreshes.

## Workflow
1. **File Loading**:
   - Reads raw transaction data from `TRANSACTION_REFRESH_FILE`.
   - Loads `LINKED_ACCOUNTS` and `LINKED_ITEMS` for enriching transactions.

2. **24-Hour Cooldown**:
   - Checks the `last_successful_update` from `LINKED_ITEMS` to determine the time since the last refresh.
   - If the last refresh was less than 24 hours ago, the function returns a message indicating the remaining cooldown time.

3. **Data Enrichment**:
   - Adds the following details to each transaction:
     - `institution_name`
     - `account_name`
     - `account_type`
     - `account_subtype`
     - `last_successful_update`

4. **Data Saving**:
   - Saves enriched transactions to `LATEST_TRANSACTIONS` in JSON format.
   - Updates the `last_successful_update` field in `LINKED_ITEMS` with the current timestamp.

5. **Error Handling**:
   - Handles missing files, invalid JSON formats, and unexpected errors with detailed logs and meaningful API responses.

## API Endpoint
- **Route**: `/process_transactions`
- **Method**: `POST`
- **Behavior**:
  - Checks for a 24-hour cooldown before proceeding.
  - Processes and saves transactions if the cooldown period has elapsed.
- **Response**:
  - Success: 
    ```json
    { "status": "success", "message": "Transactions processed successfully." }
    ```
  - Cooldown: 
    ```json
    {
      "status": "waiting",
      "message": "Last refresh was X hours ago. Please wait Y hours before refreshing again."
    }
    ```
  - Errors: Returns appropriate error messages for missing files or invalid JSON.

## Example Workflow
1. **Trigger the Function**:
   - Send a POST request after refreshing transactions to process and save them.
2. **Cooldown Check**:
   - If the last refresh occurred less than 24 hours ago, the function returns the remaining wait time.
3. **Data Enrichment**:
   - Enriches transactions with details from `LINKED_ACCOUNTS` and `LINKED_ITEMS`.
4. **Data Persistence**:
   - Saves enriched transactions to `LATEST_TRANSACTIONS`.
   - Updates the `last_successful_update` timestamp in `LINKED_ITEMS`.

## Notes
- Ensure the `TRANSACTION_REFRESH_FILE` contains the latest raw transactions before invoking this endpoint.
- This function prevents overuse of API calls through its 24-hour cooldown mechanism, ensuring optimized refresh workflows.
- The cooldown message includes clear feedback about how much time remains before the next refresh is allowed.
