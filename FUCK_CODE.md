# 🌸 Code Quality Analysis Report 🌸

## Overall Assessment

- **Quality Score**: 40.72/100
- **Quality Level**: 😷 Code reeks, mask up - Code is starting to stink, approach with caution and a mask.
- **Analyzed Files**: 198
- **Total Lines**: 23407

## Quality Metrics

| Metric | Score | Weight | Status |
|------|------|------|------|
| State Management | 17.59 | 0.20 | ✓✓ |
| Error Handling | 25.00 | 0.10 | ✓ |
| Code Structure | 30.00 | 0.15 | ✓ |
| Code Duplication | 35.00 | 0.15 | ○ |
| Comment Ratio | 42.83 | 0.15 | ○ |
| Cyclomatic Complexity | 68.53 | 0.30 | ⚠ |

## Problem Files (Top 5)

### 1. backend/app/routes/summary.py (Score: 67.89)
**Issue Categories**: 🔄 Complexity Issues:2, 📝 Comment Issues:1, ⚠️ Other Issues:1

**Main Issues**:
- Function financial_summary has very high cyclomatic complexity (24), consider refactoring
- Function 'financial_summary' () is extremely long (121 lines), must be split
- Function 'financial_summary' () complexity is severely high (24), must be simplified
- Code comment ratio is extremely low (2.22%), almost no comments

### 2. backend/app/__init__.py (Score: 64.24)
**Issue Categories**: 🔄 Complexity Issues:2, 📝 Comment Issues:1, ⚠️ Other Issues:1

**Main Issues**:
- Function create_app has very high cyclomatic complexity (20), consider refactoring
- Function 'create_app' () is extremely long (137 lines), must be split
- Function 'create_app' () complexity is severely high (20), must be simplified
- Code comment ratio is low (7.33%), consider adding more comments

### 3. backend/app/cli/sync_plaid_transactions.py (Score: 60.41)
**Issue Categories**: 🔄 Complexity Issues:4, 📝 Comment Issues:1, ⚠️ Other Issues:2

**Main Issues**:
- Function _refresh_plaid_account has high cyclomatic complexity (13), consider simplifying
- Function sync_plaid_tx has very high cyclomatic complexity (29), consider refactoring
- Function '_refresh_plaid_account' () is rather long (45 lines), consider refactoring
- Function '_refresh_plaid_account' () complexity is high (13), consider simplifying
- Function 'sync_plaid_tx' () is too long (102 lines), consider splitting
- Function 'sync_plaid_tx' () complexity is severely high (29), must be simplified
- Code comment ratio is low (5.23%), consider adding more comments

### 4. backend/app/routes/manual_io.py (Score: 59.99)
**Issue Categories**: 🔄 Complexity Issues:4, 📝 Comment Issues:1, ⚠️ Other Issues:2

**Main Issues**:
- Function auto_detect_and_upload has high cyclomatic complexity (15), consider simplifying
- Function manual_up_plaid has high cyclomatic complexity (14), consider simplifying
- Function 'auto_detect_and_upload' () is rather long (66 lines), consider refactoring
- Function 'auto_detect_and_upload' () complexity is high (15), consider simplifying
- Function 'manual_up_plaid' () is too long (74 lines), consider splitting
- Function 'manual_up_plaid' () complexity is high (14), consider simplifying
- Code comment ratio is extremely low (1.33%), almost no comments

### 5. backend/app/routes/plaid_transactions.py (Score: 59.64)
**Issue Categories**: 🔄 Complexity Issues:10, 📝 Comment Issues:1, ⚠️ Other Issues:5

**Main Issues**:
- Code comment ratio is low (5.77%), consider adding more comments
- Function exchange_public_token_endpoint has very high cyclomatic complexity (28), consider refactoring
- Function delete_plaid_account has very high cyclomatic complexity (20), consider refactoring
- Function refresh_accounts_endpoint has very high cyclomatic complexity (20), consider refactoring
- Function generate_update_link_token has very high cyclomatic complexity (18), consider refactoring
- Function sync_transactions_endpoint has very high cyclomatic complexity (21), consider refactoring
- Function 'exchange_public_token_endpoint' () is extremely long (131 lines), must be split
- Function 'exchange_public_token_endpoint' () complexity is severely high (28), must be simplified
- Function 'delete_plaid_account' () is too long (76 lines), consider splitting
- Function 'delete_plaid_account' () complexity is severely high (20), must be simplified
- Function 'refresh_accounts_endpoint' () is rather long (65 lines), consider refactoring
- Function 'refresh_accounts_endpoint' () complexity is severely high (20), must be simplified
- Function 'generate_update_link_token' () is too long (105 lines), consider splitting
- Function 'generate_update_link_token' () complexity is high (18), consider simplifying
- Function 'sync_transactions_endpoint' () is too long (107 lines), consider splitting
- Function 'sync_transactions_endpoint' () complexity is severely high (21), must be simplified

## Improvement Suggestions

### High Priority
- Keep up the clean code standards, don't let the mess creep in

### Medium Priority
- Go further—optimize for performance and readability, just because you can
- Polish your docs and comments, make your team love you even more

