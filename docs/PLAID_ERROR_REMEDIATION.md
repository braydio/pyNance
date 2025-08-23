# Plaid Error Handling and Remediation Guide [PLAID_ERRORS]

This document outlines how pyNance handles Plaid API errors, with special focus on the `ITEM_LOGIN_REQUIRED` error and automated remediation workflows.

## Overview

Plaid API errors occur when account connections become stale due to changed credentials, multi-factor authentication requirements, or security updates at the financial institution. The most common error is `ITEM_LOGIN_REQUIRED`.

## ITEM_LOGIN_REQUIRED Error

### What it means
The `ITEM_LOGIN_REQUIRED` error indicates that the user needs to re-authenticate with their financial institution. This happens when:

- User changed their online banking password
- Institution requires new multi-factor authentication
- Security policies require periodic re-authentication
- Account was temporarily locked or restricted

### How pyNance handles it

#### 1. Error Detection and Logging

When `ITEM_LOGIN_REQUIRED` occurs during account refresh:

- **Warning-level logging** (not error-level) since this is user-actionable
- **Aggregated error summaries** to reduce log noise for operators  
- **Remediation instructions** included in log messages

**Example log output:**
```
[WARNING] PNC: ITEM_LOGIN_REQUIRED - the login details of this item have changed | 
Affected accounts: 1 (Spend) | Remediation: User must re-auth via Link update mode. 
Call POST /api/plaid/transactions/generate_update_link_token with account_id.
```

#### 2. API Response Enhancement

Refresh endpoints return enhanced error information when `ITEM_LOGIN_REQUIRED` occurs:

**Single Account Refresh (`POST /api/accounts/<account_id>/refresh`):**

```json
{
  "status": "success",
  "updated": false,
  "requires_reauth": true,
  "update_link_token_endpoint": "/api/plaid/transactions/generate_update_link_token",
  "account_id": "uuid",
  "error": {
    "code": "ITEM_LOGIN_REQUIRED",
    "message": "the login details of this item have changed..."
  }
}
```

**Bulk Account Refresh (`POST /api/accounts/refresh_accounts`):**

```json
{
  "status": "success",
  "updated_accounts": [],
  "refreshed_counts": {},
  "errors": [
    {
      "institution_name": "PNC",
      "plaid_error_code": "ITEM_LOGIN_REQUIRED",
      "plaid_error_message": "the login details of this item have changed...",
      "requires_reauth": true,
      "update_link_token_endpoint": "/api/plaid/transactions/generate_update_link_token",
      "affected_account_ids": ["uuid"]
    }
  ]
}
```

#### 3. Update Link Token Generation

The new endpoint `POST /api/plaid/transactions/generate_update_link_token` creates a Plaid Link token in "update mode":

**Request:**
```json
{
  "account_id": "uuid_or_numeric_id"
}
```

**Response:**
```json
{
  "status": "success",
  "link_token": "link-sandbox-abc123...",
  "expiration": "2025-08-23T21:00:00Z",
  "account_id": "uuid"
}
```

## Frontend Integration

### Detecting Re-auth Requirements

Check API responses for the `requires_reauth` flag:

```javascript
// After account refresh
const response = await fetch('/api/accounts/refresh_accounts', {...});
const data = await response.json();

// Check for re-auth requirements
const reauthErrors = data.errors?.filter(err => err.requires_reauth);
if (reauthErrors.length > 0) {
  // Show re-auth UI
  handleReauthRequired(reauthErrors);
}
```

### Generating Update Link Token

```javascript
async function generateUpdateToken(accountId) {
  const response = await fetch('/api/plaid/transactions/generate_update_link_token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId })
  });
  
  const data = await response.json();
  if (data.status === 'success') {
    return data.link_token;
  }
  throw new Error(data.message);
}
```

### Plaid Link Update Mode Integration

```javascript
import { usePlaidLink } from 'react-plaid-link';

function ReauthModal({ accountId }) {
  const [linkToken, setLinkToken] = useState(null);
  
  useEffect(() => {
    generateUpdateToken(accountId).then(setLinkToken);
  }, [accountId]);
  
  const { open } = usePlaidLink({
    token: linkToken,
    onSuccess: (publicToken, metadata) => {
      // Handle successful re-authentication
      console.log('Re-auth successful:', metadata);
      // Optionally refresh the account again
      refreshAccount(accountId);
    },
    onExit: (error, metadata) => {
      // Handle re-auth cancellation or failure
      console.log('Re-auth cancelled:', error, metadata);
    }
  });
  
  return (
    <div>
      <p>Account needs re-authentication</p>
      <button onClick={open} disabled={!linkToken}>
        Update Account Connection
      </button>
    </div>
  );
}
```

## Account ID Flexibility

All endpoints accept account identifiers in two forms:

1. **Numeric primary key**: `17`, `42`, etc.
2. **External account_id**: `"Ej3ppQLVn0S6mL4wVwj5tADnxmDYeqSJK8b5m"`

This flexibility allows frontends to use whatever identifier they have available without additional lookups.

## Balance History Service Improvements

The balance history service has been updated to:

- **Resolve accounts by both numeric and string IDs**
- **Use warning-level logs** for missing accounts (not error-level)
- **Include processing counts** in log messages (`7 new, 3 updated`)
- **Handle datetime/date mismatches** properly when updating existing records

**Example log output:**
```
INFO - Updating balance history for Spend (17/Ej3ppQLVn0S6mL4wVwj5tADnxmDYeqSJK8b5m) from 2025-08-16 to 2025-08-22
INFO - Processed 7 balance history records (0 new, 7 updated)
```

## Operational Benefits

### For System Operators

- **Reduced log noise**: Error aggregation and warning-level logging for user-actionable errors
- **Clear remediation steps**: Log messages include specific API endpoints to call
- **Better monitoring**: Distinguish between system errors and user action requirements

### For Frontend Developers

- **Graceful error handling**: API responses include re-auth flags and endpoints
- **Consistent account resolution**: Same endpoints work with both ID formats
- **Improved user experience**: Users get clear guidance on fixing connection issues

## Monitoring and Alerting

### Log Patterns to Monitor

**Normal re-auth requirement** (WARNING level):
```
[WARNING] Institution: ITEM_LOGIN_REQUIRED - ... | Remediation: User must re-auth via Link update mode.
```

**Actual system errors** (ERROR level):
```
[ERROR] Institution: INTERNAL_SERVER_ERROR - ... | No user remediation available.
```

### Metrics to Track

- Count of `ITEM_LOGIN_REQUIRED` errors by institution
- Success rate of update link token generation
- Time to re-authentication completion
- Frequency of re-auth requirements per account

---

**Last Updated:** 2025-08-22  
**Version:** 1.0

Tag: `PLAID_ERROR_REMEDIATION_GUIDE`
