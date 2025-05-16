# Routing Refactor - Personal Changelog

** Date: 2025-05-16
*. Repo: pyNance
** Goal: Refactor modularization of backend routes

## Teastklist

[- ] Introduce `app/routes/transactions.py`
[-] Create service `app/services/transactions.py`
[- ] Move provider-specific logic to `plaid.py`, `teller.py`, etc.
[-] Register new routes in `__init__.`py

[               ] Updated on 2025-05-16 17:27