# Routing Refactor - Personal Changelog

**Date:** 2025-05-16
**Repo:** pyNance
**Goal:** Refactor modularization of backend routes

## Tasklist

- [ ] Introduce `app/routes/transactions.py`
- [ ] Create service `app/services/transactions.py`
- [ ] Move provider-specific logic to `plaid.py` and `teller.py`
- [ ] Register new routes in `__init__.py`

_Last updated: 2025-05-16 17:27_
