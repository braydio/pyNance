import csv
from datetime import datetime
import os
import traceback
from app.config import logger


def dispatch_import(filepath: str, filetype: str = "transactions"):
    """
    Dispatch an import task based on file type and format.
    """
    logger.debug(f"[IMPORT] Dispatching file: {filepath} as type: {filetype}")

    if filepath.endswith(".csv"):
        return import_transactions_from_csv(filepath)
    elif filepath.endswith(".pdf"):
        return import_transactions_from_pdf(filepath)
    else:
        logger.error(f"[IMPORT] Unsupported file format: {filepath}")
        raise ValueError(f"Unsupported file format: {filepath}")


def import_transactions_from_csv(filepath: str):
    """
    Parse a CSV export from a credit card provider like Synchrony
    Format:
    Transaction Date,Posting Date,Reference Number,Amount,Description
    """
    imported = []
    logger.debug(f"[CSV IMPORT] Starting CSV import from: {filepath}")

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logger.debug(f"[CSV IMPORT] Row: {row}")
                amount = float(row["Amount"])
                imported.append(
                    {
                        "transaction_id": row["Reference Number"],
                        "date": datetime.strptime(row["Transaction Date"], "%m/%d/%Y")
                        .date()
                        .isoformat(),
                        "name": row["Description"],
                        "amount": abs(amount),
                        "type": "credit" if amount > 0 else "debit",
                        "provider": "csv_import",
                        "currency": "USD",
                    }
                )
        logger.info(
            f"[CSV IMPORT] Successfully imported {len(imported)} transactions from CSV."
        )
        return {"status": "success", "count": len(imported), "data": imported}
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[CSV IMPORT ERROR] Failed to import CSV: {e}\n{tb}")
        return {"status": "error", "error": str(e), "traceback": tb}


def import_transactions_from_pdf(filepath: str):
    """
    Placeholder for future Synchrony PDF parser
    """
    logger.warning(f"[TODO] PDF parsing not yet implemented for {filepath}")
    return {
        "status": "pending",
        "message": "PDF parsing not implemented yet",
        "file": os.path.basename(filepath),
    }
