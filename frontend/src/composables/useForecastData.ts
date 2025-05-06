// src/composables/useForecastData.ts

import { ref, computed } from 'vue'

interface RecurringTransaction {
  account_id: string
  description: string
  amount: number
  frequency: 'monthly' | 'weekly'
  next_due_date: string
}

interface AccountHistoryPoint {
  account_id: string
  date: string
  balance: number
}

export function useForecastData() {
  const recurringTxs = ref<RecurringTransaction[]>([])
  const accountHistory = ref<AccountHistoryPoint[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const fetchData = async () => {
    loading.value = true
    error.value = null
    try {
      const [recurringRes, historyRes] = await Promise.all([
        fetch('/api/recurring-transactions'),
        fetch('/api/account-history')
      ])

      if (!recurringRes.ok || !historyRes.ok) {
        throw new Error('Failed to fetch data')
      }

      recurringTxs.value = await recurringRes.json()
      accountHistory.value = await historyRes.json()
    } catch (err) {
      error.value = err as Error
    } finally {
      loading.value = false
    }
  }

  return {
    recurringTxs: computed(() => recurringTxs.value),
    accountHistory: computed(() => accountHistory.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchData
  }
}
