// src/composables/useAccountActivity.js
/**
 * Fetch net change summary and recent transactions for an account.
 *
 * @param {Ref<string>|string|null} accountId - Account identifier
 * @returns {Object} reactive state and loader
 */
import { ref, watch, onMounted, isRef } from 'vue'
import { fetchNetChanges, fetchRecentTransactions } from '@/api/transactions'

export function useAccountActivity(accountId, limit = 5) {
  const accountIdRef = isRef(accountId) ? accountId : ref(accountId)
  const loading = ref(false)
  const error = ref(null)
  const summary = ref({ income: 0, expense: 0, net: 0 })
  const transactions = ref([])

  async function loadActivity() {
    if (!accountIdRef.value) return
    loading.value = true
    error.value = null
    try {
      const [netRes, txRes] = await Promise.all([
        fetchNetChanges(accountIdRef.value),
        fetchRecentTransactions(accountIdRef.value, limit)
      ])
      if (netRes.status === 'success') {
        summary.value = netRes.data || { income: 0, expense: 0, net: 0 }
      }
      if (txRes.status === 'success') {
        const data = txRes.data || {}
        transactions.value = data.transactions || data
      }
    } catch (e) {
      console.error('Failed to load account activity:', e)
      error.value = 'Failed to load activity'
    } finally {
      loading.value = false
    }
  }

  watch(accountIdRef, () => {
    loadActivity()
  })

  onMounted(loadActivity)

  return { accountId: accountIdRef, loading, error, summary, transactions, loadActivity }
}
