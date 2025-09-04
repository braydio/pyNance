"""Helpers for importing transaction data from external files."""

import csv
import re
import traceback
from datetime import datetime
from pathlib import Path

import pdfplumber
from app.config import logger


def _resolve_import_path(filepath: str | Path) -> Path:
    """Resolve ``filepath`` to an absolute path."""
    return Path(filepath).expanduser().resolve()


def dispatch_import(filepath: str, filetype: str = "transactions"):
    """Dispatch an import task based on file type and format."""
    path = _resolve_import_path(filepath)
    logger.debug(f"[IMPORT] Dispatching file: {path} as type: {filetype}")

    if str(path).endswith(".csv"):
        return import_transactions_from_csv(path)
    if str(path).endswith(".pdf"):
        return import_transactions_from_pdf(path)
    logger.error(f"[IMPORT] Unsupported file format: {path}")
    raise ValueError(f"Unsupported file format: {path}")


def import_transactions_from_csv(filepath: str | Path):
    """Parse a CSV export from a credit card provider like Synchrony."""
    imported = []
    path = _resolve_import_path(filepath)
    logger.debug(f"[CSV IMPORT] Starting CSV import from: {path}")

    try:
        with path.open(newline="", encoding="utf-8") as f:
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


def import_transactions_from_pdf(filepath: str | Path):
    """Parse a Synchrony PDF statement into transaction dicts."""
    path = _resolve_import_path(filepath)
    logger.debug(f"[PDF IMPORT] Starting PDF import from: {path}")

    imported = []
    try:
        with pdfplumber.open(path) as pdf:
            lines = []
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines.extend(text.splitlines())

        txn_pattern = re.compile(
            r"^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(-?\d+(?:\.\d{1,2})?)$"
        )

        for idx, line in enumerate(lines):
            match = txn_pattern.match(line.strip())
            if not match:
                continue
            date_str, desc, amt_str = match.groups()
            amount = float(amt_str.replace(",", ""))
            imported.append(
                {
                    "transaction_id": f"{date_str}-{idx}",
                    "date": datetime.strptime(date_str, "%m/%d/%Y").date().isoformat(),
                    "name": desc.strip(),
                    "amount": abs(amount),
                    "type": "credit" if amount > 0 else "debit",
                    "provider": "pdf_import",
                    "currency": "USD",
                }
            )

        logger.info(
            f"[PDF IMPORT] Successfully imported {len(imported)} transactions from PDF."
        )
        return {"status": "success", "count": len(imported), "data": imported}
    except Exception as e:  # pragma: no cover - log then return error
        tb = traceback.format_exc()
        logger.error(f"[PDF IMPORT ERROR] Failed to import PDF: {e}\n{tb}")
        return {"status": "error", "error": str(e), "traceback": tb}
