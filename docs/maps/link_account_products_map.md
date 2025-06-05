# Backend Integration Roadmap: Additional Plaid Products

## Overview
This roadmap outlines a detailed and ordered process for integrating additional Plaid products into the backend infrastructure of the `pyNance` application. The focus is on building on the existing `transactions` support to add support for:

- Investments
- Assets
- Liabilities

The product `identity` is not in scope at this time. There is also exploratory consideration for supporting **Plaid Transfer**, which enables ACH-based bank-to-bank transfers. This document assumes a backend-first implementation strategy, emphasizing modular service creation and progressive frontend enablement.

## Supported vs. Planned Plaid Products

| Product      | Status          |
|--------------|-----------------|
| Transactions | ✅ Implemented  |
| Investments  | 🚧 Planned      |
| Assets       | 🚧 Planned      |
| Liabilities  | 🚧 Planned      |
| Transfer     | 🔍 Exploratory  |
