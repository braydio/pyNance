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
    }).catch((error) => { scriptPromise = null; throw error })
  }
  return scriptPromise
}

export function usePlaidReconnect({ onSuccess, onError } = {}) {
  async function reconnect({ connectionId, accountId, onSuccess: successCallback, onError: errorCallback } = {}) {
    try {
      await loadPlaidScript()
      const payload = connectionId != null ? { connection_id: connectionId } : { account_id: accountId }
      const response = await api.generatePlaidUpdateLinkToken(payload)
      if (!response?.link_token) throw new Error(response?.message || 'Unable to start Plaid reconnect.')
      const handler = window.Plaid.create({
        token: response.link_token,
        onSuccess: async (...args) => { await (successCallback || onSuccess)?.(...args) },
        onExit: (error) => {
          const message = error?.display_message || error?.error_message
          if (message) (errorCallback || onError)?.(message)
        },
      })
      handler.open()
    } catch (error) {
      (errorCallback || onError)?.(error?.message || 'Unable to open Plaid reconnect. Please try again.')
      throw error
    }
  }
  return { reconnect }
}
