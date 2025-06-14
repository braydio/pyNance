import { ref, computed, onMounted, isRef } from 'vue'
import api from '@/services/api'

export function useTopAccounts(subtype = '') {
  const subtypeRef = isRef(subtype) ? subtype : ref(subtype)
  const accounts = ref([])
  const loading = ref(false)

  const filterSubtype = acc => {
    const val = subtypeRef.value
    return val ? (acc.subtype || '').toLowerCase() === val.toLowerCase() : true
  }

  const positiveAccounts = computed(() =>
    accounts.value
      .filter(acc => !acc.is_hidden && filterSubtype(acc) && acc.adjusted_balance >= 0)
      .sort((a, b) => b.adjusted_balance - a.adjusted_balance)
      .slice(0, 5)
  )

  const negativeAccounts = computed(() =>
    accounts.value
      .filter(acc => !acc.is_hidden && filterSubtype(acc) && acc.adjusted_balance < 0)
      .sort((a, b) => a.adjusted_balance - b.adjusted_balance)
      .slice(0, 5)
  )

  const allVisibleAccounts = computed(() => [
    ...positiveAccounts.value,
    ...negativeAccounts.value,
  ])

  const fetchAccounts = async () => {
    loading.value = true
    try {
      const data = await api.getAccounts({ include_hidden: true })
      if (data?.status === 'success') {
        accounts.value = data.accounts.map(acc => ({
          ...acc,
          adjusted_balance: acc.balance ?? 0,
        }))
      }
    } catch (err) {
      console.error('Failed to load accounts in useTopAccounts:', err)
    } finally {
      loading.value = false
    }
  }

  onMounted(fetchAccounts)

  return {
    accounts,
    positiveAccounts,
    negativeAccounts,
    allVisibleAccounts,
    loading,
    fetchAccounts,
  }
}
