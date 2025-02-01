from config import FILES, setup_logger
from helper_utils import (
    enrich_transaction,
    load_json,
    load_transactions_json,
    save_json_with_backup,
    validate_transaction,
)
from sql_utils import save_transactions_to_db

logger = setup_logger()
TRANSACTIONS_LIVE = FILES["TRANSACTIONS_LIVE"]
TRANSACTIONS_RAW = FILES["TRANSACTIONS_RAW"]


def process_transactions():
    try:
        transactions = load_transactions_json(TRANSACTIONS_RAW)
        logger.debug(f"Loaded {len(transactions)} raw transactions.")
        accounts = load_json(FILES["LINKED_ACCOUNTS"])
        items = load_json(FILES["LINKED_ITEMS"])
        enriched_transactions = []
        for tx in transactions:
            if not validate_transaction(tx):
                logger.warning(f"Skipping invalid transaction: {tx}")
                continue
            try:
                enriched_tx = enrich_transaction(tx, accounts, items)
                enriched_transactions.append(enriched_tx)
                logger.debug(f"Enriched transaction: {enriched_tx}")
            except Exception as e:
                logger.error(f"Error enriching transaction: {tx}, error: {e}")
        logger.info(f"Enriched {len(enriched_transactions)} transactions.")
        existing_data = load_transactions_json(TRANSACTIONS_LIVE)
        logger.debug(f"Loaded {len(existing_data)} existing transactions.")
        unique_transactions = {
            tx["transaction_id"]: tx for tx in (existing_data + enriched_transactions)
        }
        final_transactions = list(unique_transactions.values())
        logger.info("Saving final transactions to SQL database...")
        save_transactions_to_db(final_transactions, accounts)
        save_json_with_backup(TRANSACTIONS_LIVE, {"transactions": final_transactions})
        logger.info(
            f"Updated TRANSACTIONS_LIVE with {len(final_transactions)} transactions."
        )
        return {"status": "success", "message": "Transactions processed successfully."}
    except Exception as e:
        logger.error(f"Error in process_transactions: {e}")
        return {"status": "error", "message": str(e)}
