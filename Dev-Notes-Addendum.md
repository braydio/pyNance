```python
def save_transactions_to_db(transactions, linked_accounts):
    """
    Save transactions to the database, ensuring no duplicate entries.

    Args:
        transactions (list): List of transaction dictionaries from the Plaid API.
        linked_accounts (dict): Dictionary of linked accounts for reference to enrich data.

    Functionality:
    1. Each transaction is enriched with relevant account data from `linked_accounts`.
    2. Dates are converted from string format to `datetime.date` objects for database compatibility.
    3. Duplicate transactions are skipped based on `transaction_id` uniqueness in the database.
    4. The raw API transaction data is saved in the `raw_data` column for debugging or reference.
    5. If an error occurs (e.g., duplicate or unexpected issues), the transaction is rolled back.

    Logging:
    - Warnings are logged for duplicate transactions.
    - Errors are logged for unexpected issues during transaction processing.
    """
    for transaction in transactions:
        try:
            # Convert the date string to a datetime.date object
            transaction_date = datetime.strptime(transaction["date"], "%Y-%m-%d").date()

            # Create a new transaction object for the database
            new_transaction = Transaction(
                transaction_id=transaction["transaction_id"],  # Ensure uniqueness
                account_id=transaction["account_id"],  # Link to the account
                date=transaction_date,  # Store the transaction date
                name=transaction["name"],  # Transaction description
                amount=transaction["amount"],  # Transaction amount
                category=transaction.get("category", ["Unknown"])[-1],  # Last category item
                merchant_name=transaction.get("merchant_name", "Unknown"),  # Optional merchant
                institution_name=linked_accounts.get(transaction["account_id"], {}).get(
                    "institution_name", "Unknown"
                ),  # Enriched institution name
                raw_data=transaction,  # Full raw data stored for debugging
            )

            # Add the transaction to the session and commit
            session.add(new_transaction)
            session.commit()

        except IntegrityError:
            # Rollback the session and log a warning if the transaction ID already exists
            session.rollback()
            logging.warning(
                f"Duplicate transaction skipped: {transaction['transaction_id']}"
            )

        except Exception as e:
            # Rollback the session and log the error for unexpected issues
            session.rollback()
            logging.error(
                f"Error saving transaction {transaction['transaction_id']}: {str(e)}"
            )
```
---

```python
def save_recent_refresh_to_db(item_id, start_date, end_date, total_transactions, raw_data):
    """
    Save metadata about the recent refresh operation to the database.

    Args:
        item_id (str): The Plaid `item_id` for the linked account.
        start_date (str): The start date for the transaction refresh window.
        end_date (str): The end date for the transaction refresh window.
        total_transactions (int): The total number of transactions fetched during the refresh.
        raw_data (dict): The full raw API response for debugging or reference.

    Functionality:
    1. Creates or updates a record in the `recent_refresh` table for the specified `item_id`.
    2. Tracks key metadata like refresh dates and the total number of transactions fetched.
    3. Stores the raw API response for future debugging or compliance purposes.
    4. Prevents duplicate records by updating an existing record if `item_id` already exists.

    Logging:
    - Logs success or updates for each operation.
    - Handles and logs errors if any issues arise while saving or updating the record.
    """
    try:
        # Create a new RecentRefresh object for the database
        recent_refresh = RecentRefresh(
            item_id=item_id,  # The unique Plaid item ID
            start_date=start_date,  # Start date for the refresh
            end_date=end_date,  # End date for the refresh
            total_transactions=total_transactions,  # Total transactions fetched
            raw_data=raw_data,  # Full raw API response
        )

        # Add the refresh operation to the session and commit
        session.add(recent_refresh)
        session.commit()

    except IntegrityError:
        # If the item ID already exists, update the existing record
        session.rollback()
        try:
            existing_refresh = session.query(RecentRefresh).filter_by(item_id=item_id).one()
            existing_refresh.start_date = start_date
            existing_refresh.end_date = end_date
            existing_refresh.total_transactions = total_transactions
            existing_refresh.raw_data = raw_data
            session.commit()
            logging.info(f"Updated existing refresh record for item {item_id}.")
        except Exception as e:
            session.rollback()
            logging.error(f"Error updating recent refresh for item {item_id}: {str(e)}")

    except Exception as e:
        # Log unexpected errors and roll back the session
        session.rollback()
        logging.error(f"Error saving recent refresh for item {item_id}: {str(e)}")
```