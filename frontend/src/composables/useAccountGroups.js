// src/composables/useAccountGroups.js
/**
 * Composable for managing account groups with persistence.
 *
 * Groups and the active group identifier are loaded from and
 * stored to localStorage under the `accountGroups` key. A default
 * group is created when none exist, and the active group id always
 * points to a valid group.
 */
import { ref, watch } from 'vue'

const STORAGE_KEY = 'accountGroups'
const DEFAULT_GROUP = { id: 'group-1', name: 'Group', accounts: [] }

function cloneDefaultGroup() {
  if (typeof structuredClone === 'function') {
    return structuredClone(DEFAULT_GROUP)
  }
  return JSON.parse(JSON.stringify(DEFAULT_GROUP))
}

function resolveAccountId(account) {
  const raw =
    account && typeof account === 'object'
      ? account.id ?? account.account_id
      : account
  if (raw === null || raw === undefined) return null
  return typeof raw === 'number' ? String(raw) : raw
}

/**
 * Load groups and active id from localStorage.
 * @returns {{ groups: Array, activeGroupId: string }}
 */
function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed.groups) && parsed.groups.length) {
        return {
          groups: parsed.groups,
          activeGroupId: parsed.activeGroupId || parsed.groups[0].id,
        }
      }
    }
  } catch (e) {
    // fall back to default group on parse errors
  }
  return { groups: [cloneDefaultGroup()], activeGroupId: DEFAULT_GROUP.id }
}

/**
 * Manage account groups and active group state.
 */
export function useAccountGroups() {
  const { groups: initialGroups, activeGroupId: initialActive } = load()
  const groups = ref(initialGroups)
  const activeGroupId = ref(initialActive)

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ groups: groups.value, activeGroupId: activeGroupId.value }),
    )
  }

  function ensureActive() {
    if (!groups.value.length) {
      groups.value.push(cloneDefaultGroup())
    }
    if (!groups.value.some((g) => g.id === activeGroupId.value)) {
      activeGroupId.value = groups.value[0].id
    }
  }

  /**
   * Add a new group and set it active.
   * @param {string} name - Display name for the group.
   * @returns {string} the created group id
   */
  function addGroup(name) {
    const id = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString()
    groups.value.push({ id, name, accounts: [] })
    activeGroupId.value = id
    return id
  }

  /**
   * Set the currently active group.
   * @param {string} id
   */
  function setActiveGroup(id) {
    if (groups.value.some((g) => g.id === id)) {
      activeGroupId.value = id
    }
  }

  /**
   * Remove a group by id, ensuring at least one group remains.
   * @param {string} id
   */
  function removeGroup(id) {
    const idx = groups.value.findIndex((g) => g.id === id)
    if (idx !== -1) {
      groups.value.splice(idx, 1)
      ensureActive()
    }
  }

  /**
   * Reorder groups in the provided order.
   * @param {Array} newOrder - The reordered array of groups.
   */
  function reorderGroups(newOrder) {
    groups.value = [...newOrder]
  }

  /**
   * Add an account to a group enforcing a max of five accounts.
   * @param {string} groupId
   * @param {unknown} account
   * @returns {boolean} true if the account was added
   */
  function addAccountToGroup(groupId, account) {
    const group = groups.value.find((g) => g.id === groupId)
    if (!group || group.accounts.length >= 5) return false
    const accountId = resolveAccountId(account)
    if (!accountId) return false
    if (group.accounts.some((a) => resolveAccountId(a) === accountId)) {
      return false
    }
    if (typeof account === 'object') {
      group.accounts.push({ ...account, id: accountId })
    } else {
      group.accounts.push({ id: accountId })
    }
    return true
  }

  /**
   * Remove an account from a group by account identifier.

   * @param {string} groupId
   * @param {string} accountId
   * @returns {boolean} true if the account was removed
   */
  function removeAccountFromGroup(groupId, accountId) {
    const group = groups.value.find((g) => g.id === groupId)
    if (!group) return false
    const resolvedId = resolveAccountId(accountId)
    const idx = group.accounts.findIndex((a) => resolveAccountId(a) === resolvedId)
    if (idx === -1) return false
    group.accounts.splice(idx, 1)
    return true
  }

  watch(
    groups,
    () => {
      ensureActive()
      persist()
    },
    { deep: true },
  )
  watch(activeGroupId, persist)
  ensureActive()
  persist()

  return {
    groups,
    activeGroupId,
    addGroup,
    setActiveGroup,
    removeGroup,

    reorderGroups,

    addAccountToGroup,
    removeAccountFromGroup,
  }
}
