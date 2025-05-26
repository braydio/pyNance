# Frontend Duplicate Component Review 

This document tracks likely duplicated or unclear components for review and cleaning.


```text
Component | Role | Action
----------- |---------- |-------------------
@AccountsTable.vue | Std table | 最 Preserved, main version
@AccountsTableLite.vue  | Stubview partial copy | 开 likely placeholder - consider deleting
@LinkAccount.vue  | Account Link buttons  | 最 Refactored active file with content
@LinkAccountFullProducts.vue  | Empty file probably not used | 昋 Delete if unused
PRefreshControls.vue | Shared wrapper? | 最 Review for redendancy
RRefreshPlaidControls.vue | Plaid specific  | 最 Refactorer component?


UploadCSV.vue vs UploadDownloadCSV.vue | Sizes match, function may overlap | 最 Merge into one
```

Likely obsolete:
 - AccountsTableLite.vue (1-byte dommy file)
 - LinkAccountFullProducts.vue (empty)
 - backups/ (staging or deprecated)


Tasks:
 1. Grep for component usages:
    `grep -r "LinkAccountFullProducts" frontend/src``

 2. Merge URL and DownloadCSV files with similar size and flags;
    - Strong candidates by input token
    - Share styles and bland layout


       