/**
 * Composable for selecting accounts with sanitized logging.
 */
import { ref, computed, onMounted } from 'vue'
import { sanitizeForLog } from '../utils/sanitize.js'

export function useAccountSelector() {
  const allAccounts = ref([])
  const selectedAccountIds = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Computed properties
  const selectedAccounts = computed(() =>
    allAccounts.value.filter((account) => selectedAccountIds.value.includes(account.account_id)),
  )

  const availableAccounts = computed(() =>
    allAccounts.value.map((account) => ({
      id: account.account_id,
      name: account.name,
      type: account.type,
      subtype: account.subtype,
      institution_name: account.institution_name,
      mask: account.mask,
      balance: account.adjusted_balance || account.balance || 0,
      institution_icon_url: account.institution_icon_url,
    })),
  )

  const hasSelection = computed(() => selectedAccountIds.value.length > 0)

  // Methods
  /**
   * Retrieve accounts from API and update state.
   * Logs sanitized account count on success.
   */
  async function fetchAccounts() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch('/api/accounts/get_accounts')
      const data = await response.json()

      if (data.status === 'success' && data.accounts) {
        allAccounts.value = data.accounts
        console.log(`Loaded ${sanitizeForLog(data.accounts.length)} accounts for selector`)
      } else {
        throw new Error(data.message || 'Failed to fetch accounts')
      }
    } catch (e) {
      console.error('Error fetching accounts:', sanitizeForLog(e.message || e))
      error.value = e.message || 'Failed to fetch accounts'
    } finally {
      loading.value = false
    }
  }

  function selectAccount(accountId) {
    if (!selectedAccountIds.value.includes(accountId)) {
      selectedAccountIds.value.push(accountId)
    }
  }

  function deselectAccount(accountId) {
    selectedAccountIds.value = selectedAccountIds.value.filter((id) => id !== accountId)
  }

  function toggleAccount(accountId) {
    if (selectedAccountIds.value.includes(accountId)) {
      deselectAccount(accountId)
    } else {
      selectAccount(accountId)
    }
  }

  function selectAll() {
    selectedAccountIds.value = allAccounts.value.map((account) => account.account_id)
  }

  function deselectAll() {
    selectedAccountIds.value = []
  }

  function selectAccountsByType(type) {
    const accountIds = allAccounts.value
      .filter((account) => account.type === type)
      .map((account) => account.account_id)

    selectedAccountIds.value = [...new Set([...selectedAccountIds.value, ...accountIds])]
  }

  // Auto-load accounts on mount
  onMounted(() => {
    fetchAccounts()
  })

  return {
    // State
    allAccounts,
    selectedAccountIds,
    loading,
    error,

    // Computed
    selectedAccounts,
    availableAccounts,
    hasSelection,

    // Methods
    fetchAccounts,
    selectAccount,
    deselectAccount,
    toggleAccount,
    selectAll,
    deselectAll,
    selectAccountsByType,
  }
}
