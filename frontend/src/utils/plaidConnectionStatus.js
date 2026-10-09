export function normalizeConnectionStatus(status) {
  if (!status || status.provider !== 'plaid') return null
  const requiresReauth = Boolean(status.requires_reauth || status.state === 'reauth_required')
  return {
    ...status,
    state: requiresReauth ? 'reauth_required' : 'healthy',
    requires_reauth: requiresReauth,
  }
}

export function uniqueReconnectConnections(accounts = []) {
  const connections = new Map()
  accounts.forEach((account) => {
    const status = normalizeConnectionStatus(account.connection_status)
    if (!status?.requires_reauth) return
    const connectionId = status.connection_id
    const accountId = account.account_id
    if (connectionId == null && accountId == null) return
    const key =
      connectionId == null ? `account:${String(accountId)}` : `connection:${String(connectionId)}`
    if (!connections.has(key))
      connections.set(key, {
        connectionId,
        accountId: connectionId == null ? accountId : undefined,
        key,
        status,
        accounts: [],
      })
    connections.get(key).accounts.push(account)
  })
  return [...connections.values()]
}
