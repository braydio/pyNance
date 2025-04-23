import csv
from datetime import datetime
import os


def dispatch_import(filepath: str, filetype: str = "transactions"):
    """
    Dispatch an import task based on file type and format.
    """
    if filepath.endswith(".csv"):
        return import_transactions_from_csv(filepath)
    elif filepath.endswith(".pdf"):
        return import_transactions_from_pdf(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath}")


def import_transactions_from_csv(filepath: str):
    """
    Parse a CSV export from a credit card provider like Synchrony
    Format:
    Transaction Date,Posting Date,Reference Number,Amount,Description
    """
    imported = []
    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
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
                        "provider": "pdf_import",
                        "currency": "USD",
                        # account_id or user_id should be filled in by calling logic
                    }
                )
        return {"status": "success", "count": len(imported), "data": imported}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def import_transactions_from_pdf(filepath: str):
    """
    Placeholder for future Synchrony PDF parser
    """
    print(f"[TODO] PDF parsing not yet implemented for {filepath}")
    return {
        "status": "pending",
        "message": "PDF parsing not implemented yet",
        "file": os.path.basename(filepath),
    }
