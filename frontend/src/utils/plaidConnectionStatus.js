export function normalizeConnectionStatus(status) {
  if (!status || status.provider !== 'plaid') return null
  const requiresReauth = Boolean(status.requires_reauth || status.state === 'reauth_required')
  return {
    ...status,
    state: requiresReauth ? 'reauth_required' : 'healthy',
    requires_reauth: requiresReauth,
  }
}

function connectionKey(connectionId, accountId) {
  return connectionId == null
    ? `account:${String(accountId)}`
    : `connection:${String(connectionId)}`
}

function newGroup(connectionId, accountId, status) {
  return {
    key: connectionKey(connectionId, accountId),
    connectionId,
    accountId: connectionId == null ? accountId : undefined,
    status,
    accounts: [],
    accountIds: [],
    errors: [],
  }
}

function addAccount(group, account) {
  if (group.accountIds.includes(account.account_id)) return
  group.accounts.push(account)
  group.accountIds.push(account.account_id)
}

/**
 * Group accounts that need Plaid reauthentication by Plaid Item (`connection_id`).
 *
 * One group is one Link update session. Persisted `connection_status` is the authority;
 * live refresh `errors` only add a group for accounts whose persisted status is unknown,
 * so a stale refresh error cannot override a healthy Item. Separate Items at one
 * institution stay separate, and accounts with no Item identity are never merged.
 *
 * @param {Array<object>} accounts Loaded accounts, each optionally with `connection_status`.
 * @param {Array<object>} refreshErrors Optional `errors` from a refresh response.
 * @returns {Array<object>} Groups: `{ key, connectionId, accountId, status, accounts, accountIds, errors }`.
 */
export function reconnectConnectionGroups(accounts = [], refreshErrors = []) {
  const groups = new Map()
  const byAccountId = new Map(accounts.map((account) => [String(account.account_id), account]))

  accounts.forEach((account) => {
    const status = normalizeConnectionStatus(account.connection_status)
    if (!status?.requires_reauth) return
    const connectionId = status.connection_id
    if (connectionId == null && account.account_id == null) return
    const key = connectionKey(connectionId, account.account_id)
    if (!groups.has(key)) groups.set(key, newGroup(connectionId, account.account_id, status))
    addAccount(groups.get(key), account)
  })

  refreshErrors.forEach((error) => {
    if (!error?.requires_reauth && error?.plaid_error_code !== 'ITEM_LOGIN_REQUIRED') return
    ;(error.account_ids || []).forEach((id) => {
      const account = byAccountId.get(String(id))
      if (!account) return
      const persisted = normalizeConnectionStatus(account.connection_status)
      // Fresh persisted health wins over an ephemeral refresh error.
      if (persisted && !persisted.requires_reauth) return
      const connectionId = persisted?.connection_id ?? error.connection_id
      const key = connectionKey(connectionId, account.account_id)
      if (!groups.has(key)) {
        groups.set(
          key,
          newGroup(connectionId, account.account_id, {
            provider: 'plaid',
            state: 'reauth_required',
            requires_reauth: true,
            connection_id: connectionId,
          }),
        )
      }
      const group = groups.get(key)
      addAccount(group, account)
      const message = error.plaid_error_message || error.plaid_error_code
      if (message && !group.errors.includes(message)) group.errors.push(message)
    })
  })

  // Siblings of a repaired Item share its connection_id, so include them all.
  groups.forEach((group) => {
    if (group.connectionId == null) return
    accounts.forEach((account) => {
      const status = normalizeConnectionStatus(account.connection_status)
      if (String(status?.connection_id) === String(group.connectionId)) addAccount(group, account)
    })
  })

  return [...groups.values()]
}

export function uniqueReconnectConnections(accounts = []) {
  return reconnectConnectionGroups(accounts)
}
