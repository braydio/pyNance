/**
 * Composable to fetch and expose transaction history for a single account.
 * Similar to DailyNet data but filtered for a specific account.
 */
import { ref, isRef, watch } from 'vue'
import { fetchAccountTransactionHistory } from '@/api/accounts'

/**
 * Reactive helper to load recent transaction history for an account.
 * @param {import('vue').Ref<string> | string} accountId
 */
export function useAccountTransactionHistory(accountId) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  const history = ref([])
  const loading = ref(false)

  const fetchHistory = async () => {
    if (!accountIdRef.value) return
    loading.value = true
    try {
      const response = await fetchAccountTransactionHistory(accountIdRef.value)
      let hist = []
      if (Array.isArray(response?.data?.history)) {
        hist = response.data.history
      } else if (Array.isArray(response?.history)) {
        hist = response.history
      } else if (Array.isArray(response?.data?.data?.history)) {
        hist = response.data.data.history
      }
      history.value = hist
    } catch (err) {
      console.error('Failed to load account transaction history:', err)
      // Fallback to empty array to prevent sparkline errors
      history.value = []
    } finally {
      loading.value = false
    }
  }

  watch(accountIdRef, fetchHistory, { immediate: true })

  return {
    history,
    loading,
    fetchHistory,
  }
}
