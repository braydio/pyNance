// src/composables/useSnapshotAccounts.js
/**
 * Manage selected accounts for the dashboard snapshot view.
 * Fetches persisted selections, account data, and upcoming recurring reminders.
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'
import axios from 'axios'

const REMINDER_PATH = id => `/api/recurring/${id}/recurring`

export function useSnapshotAccounts(fallbackMaxSelection = 5) {
  const accounts = ref([])
  const selectedIds = ref([])
  const reminders = ref({})
  const metadata = ref({})

  const isLoading = ref(false)
  const isSaving = ref(false)
  const remindersLoading = ref(false)
  const error = ref(null)

  const initialized = ref(false)
  const lastPersisted = ref([])
  let reminderRequestId = 0

  const maxSelection = computed(
    () => metadata.value?.max_selection || fallbackMaxSelection,
  )

  const selectedAccounts = computed(() =>
    selectedIds.value
      .map(id => accounts.value.find(account => account.account_id === id))
      .filter(Boolean),
  )

  const availableAccounts = computed(() =>
    accounts.value.filter(account => !selectedIds.value.includes(account.account_id)),
  )

  const snapshotReady = computed(() => initialized.value && !isLoading.value)

  const areIdsEqual = (a = [], b = []) => {
    if (a.length !== b.length) return false
    return a.every((val, idx) => val === b[idx])
  }

  const loadSnapshot = async () => {
    const wasInitialized = initialized.value
    initialized.value = false
    isLoading.value = true
    error.value = null
    try {
      const response = await api.getAccountSnapshot()
      if (response?.status !== 'success') {
        throw new Error(response?.message || 'Unable to load snapshot preferences')
      }
      const data = response.data || {}
      accounts.value = (data.available_accounts || []).slice()
      metadata.value = data.metadata || {}

      const serverSelection = (data.selected_account_ids || []).slice(0, maxSelection.value)
      selectedIds.value = serverSelection
      lastPersisted.value = serverSelection.slice()

      if (!serverSelection.length && accounts.value.length) {
        const fallback = accounts.value
          .slice(0, maxSelection.value)
          .map(account => account.account_id)
        selectedIds.value = fallback
        lastPersisted.value = []
        await persistSelection(fallback)
      }
    } catch (err) {
      error.value = err
      console.error('Failed to load snapshot preferences', err)
    } finally {
      isLoading.value = false
      initialized.value = wasInitialized
    }
  }

  const persistSelection = async ids => {
    const limited = ids.slice(0, maxSelection.value)
    if (areIdsEqual(limited, lastPersisted.value)) {
      return
    }

    isSaving.value = true
    error.value = null
    try {
      const response = await api.updateAccountSnapshot({
        selected_account_ids: limited,
      })
      if (response?.status !== 'success') {
        throw new Error(response?.message || 'Unable to update snapshot selection')
      }
      const data = response.data || {}
      if (Array.isArray(data.available_accounts)) {
        accounts.value = data.available_accounts.slice()
      }
      metadata.value = { ...metadata.value, ...(data.metadata || {}) }
      const persisted = (data.selected_account_ids || limited).slice(0, maxSelection.value)
      lastPersisted.value = persisted
      if (!areIdsEqual(selectedIds.value, persisted)) {
        initialized.value = false
        selectedIds.value = persisted
        initialized.value = true
      }
    } catch (err) {
      error.value = err
      console.error('Failed to persist snapshot selection', err)
      throw err
    } finally {
      isSaving.value = false
    }
  }

  const fetchReminders = async () => {
    if (!snapshotReady.value || !selectedIds.value.length) {
      reminders.value = {}
      return
    }

    reminderRequestId += 1
    const requestId = reminderRequestId
    remindersLoading.value = true
    try {
      const entries = await Promise.all(
        selectedIds.value.map(async accountId => {
          try {
            const res = await axios.get(REMINDER_PATH(accountId))
            if (res.data?.status === 'success') {
              return [accountId, res.data.reminders || []]
            }
          } catch (err) {
            console.error(`Failed to load reminders for ${accountId}`, err)
          }
          return [accountId, []]
        }),
      )
      if (requestId === reminderRequestId) {
        reminders.value = Object.fromEntries(entries)
      }
    } finally {
      if (requestId === reminderRequestId) {
        remindersLoading.value = false
      }
    }
  }

  const handleSelectionChange = ids => {
    if (!initialized.value) {
      return
    }
    const limited = ids.slice(0, maxSelection.value)
    if (!areIdsEqual(ids, limited)) {
      selectedIds.value = limited
      return
    }

    persistSelection(limited)
      .catch(() => {})
      .finally(() => {
        fetchReminders()
      })
  }

  watch(selectedIds, handleSelectionChange, { deep: false })

  onMounted(async () => {
    await loadSnapshot()
    initialized.value = true
    if (selectedIds.value.length) {
      fetchReminders()
    }
  })

  const addAccount = accountId => {
    if (!accountId) return
    if (selectedIds.value.includes(accountId)) return
    const limit = maxSelection.value
    if (selectedIds.value.length >= limit) {
      const next = selectedIds.value.slice(1)
      selectedIds.value = [...next, accountId]
    } else {
      selectedIds.value = [...selectedIds.value, accountId]
    }
  }

  const removeAccount = accountId => {
    selectedIds.value = selectedIds.value.filter(id => id !== accountId)
  }

  const setSelection = ids => {
    selectedIds.value = (ids || []).slice(0, maxSelection.value)
  }

  return {
    accounts,
    selectedAccounts,
    selectedIds,
    reminders,
    metadata,
    maxSelection,
    availableAccounts,
    isLoading,
    isSaving,
    remindersLoading,
    error,
    addAccount,
    removeAccount,
    setSelection,
    refreshSnapshot: loadSnapshot,
    refreshReminders: fetchReminders,
  }
}
