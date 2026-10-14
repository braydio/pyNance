import { ref } from 'vue'
import api from '@/services/api'

let scriptPromise
function loadPlaidScript() {
  if (window.Plaid) return Promise.resolve()
  if (!scriptPromise) {
    scriptPromise = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-plaid-link]')
      const script = existing || document.createElement('script')
      script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
      script.async = true
      script.dataset.plaidLink = 'true'
      script.onload = resolve
      script.onerror = reject
      if (!existing) document.head.appendChild(script)
    }).catch((error) => {
      scriptPromise = null
      throw error
    })
  }
  return scriptPromise
}

// At most one Link session may be live app-wide. `activeKey` is reactive so every
// reconnect button can show it as busy.
let activeSession = null
const activeKey = ref(null)

function sessionKey(connectionId, accountId) {
  return connectionId != null
    ? `connection:${String(connectionId)}`
    : `account:${String(accountId)}`
}

function diagnostic(stage, key, extra = {}) {
  console.debug('[plaid-reconnect]', stage, { key, ...extra })
}

/**
 * Plaid Link update-mode coordinator.
 *
 * `reconnect()` resolves once with `{ status, message? }` where status is one of
 * `verified` (Link succeeded and the verification callback finished), `cancelled`
 * (clean exit), `failed` (script/token/Link/verification error) or `busy` (a different
 * connection already has Link open). It never rejects. Calling it again for the active
 * connection returns the in-flight promise instead of starting a second session.
 *
 * @param {{ onSuccess?: Function, onError?: Function }} [defaults]
 */
export function usePlaidReconnect({ onSuccess, onError } = {}) {
  function reconnect({
    connectionId,
    accountId,
    accountCount,
    onSuccess: successCallback,
    onError: errorCallback,
  } = {}) {
    const key = sessionKey(connectionId, accountId)
    if (activeSession) {
      if (activeSession.key === key) return activeSession.promise
      return Promise.resolve({
        status: 'busy',
        activeKey: activeSession.key,
        message: 'Finish the open Plaid window before reconnecting another connection.',
      })
    }

    const fail = errorCallback || onError
    const verify = successCallback || onSuccess
    const session = { key }
    activeSession = session
    activeKey.value = key

    session.promise = new Promise((resolve) => {
      let settled = false
      let succeeded = false
      const settle = (result) => {
        if (settled) return
        settled = true
        diagnostic('settled', key, { outcome: result.status, accounts: accountCount })
        resolve(result)
      }
      const failWith = (message) => {
        try {
          fail?.(message)
        } catch (callbackError) {
          console.error('Plaid reconnect error callback failed', callbackError)
        }
        settle({ status: 'failed', message })
      }

      ;(async () => {
        diagnostic('preparing', key, { accounts: accountCount })
        await loadPlaidScript()
        const payload =
          connectionId != null ? { connection_id: connectionId } : { account_id: accountId }
        const response = await api.generatePlaidUpdateLinkToken(payload)
        if (!response?.link_token)
          throw new Error(response?.message || 'Unable to start Plaid reconnect.')
        const handler = window.Plaid.create({
          token: response.link_token,
          onSuccess: async (...args) => {
            succeeded = true
            diagnostic('verifying', key)
            try {
              await verify?.(...args)
              settle({ status: 'verified' })
            } catch (error) {
              failWith(error?.message || 'Unable to verify the Plaid connection.')
            }
          },
          onExit: (error) => {
            // Plaid may report exit after success; the success path owns the outcome.
            if (succeeded || settled) return
            const message = error?.display_message || error?.error_message
            if (message) failWith(message)
            else settle({ status: 'cancelled' })
          },
        })
        diagnostic('open', key)
        handler.open()
      })().catch((error) => {
        failWith(error?.message || 'Unable to open Plaid reconnect. Please try again.')
      })
    }).finally(() => {
      if (activeSession === session) {
        activeSession = null
        activeKey.value = null
      }
    })
    return session.promise
  }
  return { reconnect, activeKey }
}
