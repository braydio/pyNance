#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

EXPECTED = {
    "backend/.env.example": {
        "ENV": "development",
        "LOG_LEVEL": "INFO",
        "SQL_ECHO": "false",
        "CLIENT_NAME": "pyNance-Dash",
        "ENABLE_ARBIT_DASHBOARD": "false",
        "BACKEND_PUBLIC_URL": "https://example.invalid",
        "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://user:password@localhost:5432/pynance",
        "PLAID_CLIENT_ID": "REPLACE_ME",
        "PLAID_SECRET_KEY": "REPLACE_ME",
        "PLAID_SECRET": "REPLACE_ME",
        "PLAID_ENV": "sandbox",
        "PLAID_WEBHOOK_SECRET": "REPLACE_ME",
        "PLAID_CLIENT_NAME": "pyNance-Dash",
        "PRODUCTS": "transactions",
        "PHONE_NBR": "+10000000000",
        "FIDELITY_USERNAME": "REPLACE_ME",
        "FIDELITY_PASSWORD": "REPLACE_ME",
        "FIDELITY_TOTP_SECRET": "REPLACE_ME",
        "VARIABLE_ENV_TOKEN": "REPLACE_ME",
        "VARIABLE_ENV_ID": "REPLACE_ME",
        "CHROMA_COLLECTION": "pynance-code",
        "CHROMA_RESULT_COUNT": "3",
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8055",
        "CHROMA_MODEL": "all-MiniLM-L6-v2",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333",
        "QDRANT_COLLECTION": "pynance-code",
        "QDRANT_URL": "http://localhost:6333",
        "LOCALAI_URL": "http://localhost:5051",
        "LOCALAI_MODEL": "REPLACE_ME",
        "TEXTGEN_URL": "http://localhost:5051",
        "RETRIEVAL_LIMIT": "5",
        "MAX_ITERATIONS": "10",
        "RETRY_DELAY": "1.0",
    },
    "frontend/.env.example": {
        "VITE_SESSION_MODE": "development",
        "VITE_APP_API_BASE_URL": "http://localhost:5000/api",
        "VITE_PLAID_CLIENT_ID": "REPLACE_ME",
        "VITE_USER_ID_PLAID": "REPLACE_ME",
        "PHONE_NBR": "+10000000000",
    },
}


def parse_env(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8").splitlines()
    parsed: dict[str, str] = {}
    for line in raw:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            raise ValueError(f"Invalid line (missing '='): {line}")
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid line (empty key): {line}")
        if key in parsed:
            raise ValueError(f"Duplicate key {key!r}")
        parsed[key] = value
    return parsed


def check_file(path_str: str, expected: dict[str, str]) -> list[str]:
    path = Path(path_str)
    errors: list[str] = []
    if not path.exists():
        return [f"Missing file: {path_str}"]

    try:
        parsed = parse_env(path)
    except ValueError as exc:
        return [f"{path_str}: {exc}"]

    extra = sorted(set(parsed) - set(expected))
    missing = sorted(set(expected) - set(parsed))

    if missing:
        errors.append(f"{path_str}: missing keys: {', '.join(missing)}")
    if extra:
        errors.append(f"{path_str}: unexpected keys: {', '.join(extra)}")

    for key, expected_value in expected.items():
        if key not in parsed:
            continue
        actual_value = parsed[key]
        if actual_value != expected_value:
            errors.append(
                f"{path_str}: {key} should be {expected_value!r} but found {actual_value!r}"
            )

    return errors


def main() -> int:
    failures: list[str] = []
    for path_str, expected in EXPECTED.items():
        failures.extend(check_file(path_str, expected))

    if failures:
        print("[ENV] Example env files do not match the approved safe template:")
        for entry in failures:
            print(f"- {entry}")
        return 1

    print("[ENV] Example env files match the approved safe template.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
