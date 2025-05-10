# 📦 API Migration Plan: `services/api.js` ➡️ `api/`

## 🧭 Overview

We are decomposing the monolithic `services/api.js` file into logically grouped modules under `src/api/`. This enables:

- Clearer domain ownership
- Easier testability and error isolation
- Cleaner import paths for component usage

---

## ✅ Migration Checklist

### 🔹 `api/transactions.js`

- [ ] `fetchTransactions`
- [ ] `updateTransaction`
- [ ] `exchangePublicToken` _(move to `plaid.js`)_
- [ ] `generateLinkToken` _(move to `plaid.js`)_
- [ ] `saveTellerToken` _(move to `teller.js`)_

### 🔹 `api/charts.js`

# 📦 API Migration Plan: `services/api.js` ➡️ `api/`

## 🧭 Overview

We are decomposing the monolithic `services/api.js` file into logically grouped modules under `src/api/`. This enables:

- Clearer domain ownership
- Easier testability and error isolation
- Cleaner import paths for component usage

---

## ✅ Migration Checklist

### 🔹 `api/transactions.js`

- [x] MOVED: `fetchTransactions`
- [x] MOVED: `updateTransaction`
- [ ] DEPRECATION BEGIN: Remove from `services/api.js`
- [ ] Check external files for old imports
- [ ] Add deprecation warning in `services/api.js`
- [ ] Confirm deletion from `services/api.js`

### 🔹 `api/charts.js`

- [x] MOVED: `fetchCategoryBreakdown`
- [x] MOVED: `fetchDailyNet`
- [x] MOVED: `fetchNetAssets`
- [ ] DEPRECATION BEGIN
- [ ] Check external files for old imports
- [ ] Add deprecation warning
- [ ] Confirm deletion

### 🔹 `api/accounts.js`

- [x] MOVED: `getAccounts`
- [x] MOVED: `refreshAccounts`
- [x] MOVED: `deleteAccount`
- [ ] DEPRECATION BEGIN
- [ ] Check external files for old imports
- [ ] Add deprecation warning
- [ ] Confirm deletion

### 🔹 `api/plaid.js`

- [ ] MOVED: `exchangePublicToken`
- [ ] MOVED: `generateLinkToken`
- [ ] DEPRECATION BEGIN
- [ ] Check external files for old imports
- [ ] Add deprecation warning
- [ ] Confirm deletion

### 🔹 `api/teller.js`

- [ ] MOVED: `saveTellerToken`
- [ ] DEPRECATION BEGIN
- [ ] Check external files for old imports
- [ ] Add deprecation warning
- [ ] Confirm deletion

---

## 🧪 Test Checklist

After moving each function:

- [ ] Update **all import paths** across components
- [ ] Run app to confirm no console or import errors
- [ ] Confirm API calls return successfully
- [ ] Confirm errors are caught and logged consistently

---

## 📁 Destination Folder Layout

```sh
frontend/src/api/
├── accounts.js
├── charts.js
├── plaid.js
├── recurring.js
├── teller.js
└── transactions.js
```

---

_Last updated: 2025-05-06_
