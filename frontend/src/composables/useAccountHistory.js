/**
 * Composable to fetch and expose balance history for a single account.
 */
import { ref, isRef, watch } from 'vue'
import { fetchAccountHistory } from '@/api/accounts'

/**
 * Reactive helper to load recent balance history for an account.
 * @param {import('vue').Ref<string> | string} accountId
 */
export function useAccountHistory(accountId) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  const history = ref([])
  const loading = ref(false)

  const fetchHistory = async () => {
    if (!accountIdRef.value) return
    loading.value = true
    try {
      const response = await fetchAccountHistory(accountIdRef.value)
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
      console.error('Failed to load account history:', err)
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
