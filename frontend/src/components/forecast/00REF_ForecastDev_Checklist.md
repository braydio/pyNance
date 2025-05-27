
## 🧮 Forecast Engine: Goal-Based Implementation Plan

A step-by-step guide to implementing a forecast engine using the `pyNance` repo, from concept to production deployment.

---

## 📁 Goal 1: Ingest & Structure Data

- [x] Thread `user_id` through fronten api -> recurring -summary support
- [x] Verify `account_history` sources for actuals -> chart validation

---

## 📀 Goal 2.5 - Runtime: Switches & Validation
- [x] Live/mock toggle switcher for refresh_all_accounts
- [x] Manual adjustment from VUE -> forecast calculation lines
- [x] Dashboard toggle for manual/mock mode

---

## 🚊 Checklist Updates

- [x] Revised dev check list to include fronten-level toggles in chart
- [x] Confirmed calculation endpoints are returning `labels`, `actuals`, from `account_history`
- [x] Checked for wiring logic/validation status via recurring_transactions.
