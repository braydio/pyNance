// src/composables/useSnapshotAccounts.js
/**
 * Manage selected accounts for the dashboard snapshot view.
 * Fetches account data and upcoming recurring reminders.
 */
import { ref, computed, watch, onMounted } from 'vue'
import api from '@/services/api'
import axios from 'axios'

export function useSnapshotAccounts(maxSelection = 5) {
  const accounts = ref([])
  const selectedIds = ref([])
  const reminders = ref({})

  function initSelection() {
    const stored = localStorage.getItem('snapshotAccounts')
    if (stored) {
      try {
        selectedIds.value = JSON.parse(stored).slice(0, maxSelection)
      } catch {
        selectedIds.value = []
      }
    } else if (accounts.value.length) {
      selectedIds.value = accounts.value.slice(0, maxSelection).map(a => a.account_id)
    }
  }

  const loadAccounts = async () => {
    try {
      const res = await api.getAccounts()
      if (res.status === 'success') {
        accounts.value = res.accounts
          .slice()
          .sort((a, b) => {
            const aName = `${a.institution_name || ''} ${a.name}`.trim()
            const bName = `${b.institution_name || ''} ${b.name}`.trim()
            return aName.localeCompare(bName)
          })
        initSelection()
      }
    } catch (err) {
      console.error('Failed to load accounts', err)
    }
  }

  const fetchReminders = async () => {
    const all = {}
    for (const id of selectedIds.value) {
      try {
        const res = await axios.get(`/api/recurring/${id}/recurring`)
        if (res.data.status === 'success') {
          all[id] = res.data.reminders
        }
      } catch (err) {
        console.error('Failed to load reminders for', id, err)
      }
    }
    reminders.value = all
  }

  watch(
    selectedIds,
    val => {
      localStorage.setItem('snapshotAccounts', JSON.stringify(val.slice(0, maxSelection)))
      fetchReminders()
    },
    { deep: true }
  )

  onMounted(async () => {
    await loadAccounts()
    if (selectedIds.value.length) {
      fetchReminders()
    }
  })

  const selectedAccounts = computed(() =>
    accounts.value.filter(acc => selectedIds.value.includes(acc.account_id))
  )

  return { accounts, selectedAccounts, selectedIds, reminders, loadAccounts }
}
