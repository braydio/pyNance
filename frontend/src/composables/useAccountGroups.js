// src/composables/useAccountGroups.js
/**
 * Manage account groups and active group state for account displays.
 * Ensures at least one group exists and the active group id always
 * references a valid group.
 */
import { ref, watch } from 'vue'

export function useAccountGroups() {
  const groups = ref([
    { id: 'assets', name: 'Assets', accounts: [] },
    { id: 'liabilities', name: 'Liabilities', accounts: [] },
  ])

  const activeGroupId = ref(groups.value[0].id)

  function ensureActive() {
    if (!groups.value.length) {
      groups.value.push({ id: 'default', name: 'Group', accounts: [] })
    }
    if (!groups.value.some(g => g.id === activeGroupId.value)) {
      activeGroupId.value = groups.value[0].id
    }
  }

  watch(groups, ensureActive, { deep: true })
  ensureActive()

  return { groups, activeGroupId }
}
