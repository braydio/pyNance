// src/composables/useAccountGroups.js
/**
 * Composable for managing account groups persisted via the backend API.
 *
 * Provides reactive state for groups and the active group identifier along
 * with helper methods for creating, updating, deleting, and reordering groups
 * and their accounts. All mutations are performed optimistically and rolled
 * back if the corresponding API call fails.
 */

import { ref } from 'vue'
import api from '@/services/api'

const DEFAULT_GROUP_NAME = 'Group'
const DEFAULT_ACCENT = 'var(--color-accent-cyan)'
const MAX_ACCOUNTS_PER_GROUP = 5
const STORAGE_BASE_KEY = 'pynance.account-groups'

function generateId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `group-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function resolveAccountId(account) {
  // Prefer the external account_id over internal numeric id
  const raw = account && typeof account === 'object' ? (account.account_id ?? account.id) : account
  if (raw === null || raw === undefined) return null
  return typeof raw === 'number' ? String(raw) : String(raw)
}

function normalizeAccount(account) {
  if (!account || typeof account !== 'object') return null
  const id = resolveAccountId(account)
  if (!id) return null
  return {
    ...account,
    id,
    account_id: account.account_id ?? id,
  }
}

function normalizeAccounts(list) {
  if (!Array.isArray(list)) return []
  const seen = new Set()
  const normalized = []
  for (const entry of list) {
    const normalizedEntry = normalizeAccount(entry)
    if (!normalizedEntry) continue
    if (seen.has(normalizedEntry.id)) continue
    seen.add(normalizedEntry.id)
    normalized.push(normalizedEntry)
  }
  return normalized
}

function normalizeGroup(raw) {
  const baseId = raw?.id ? String(raw.id) : generateId()
  return {
    id: baseId,
    name: raw?.name || DEFAULT_GROUP_NAME,
    accent: raw?.accent || DEFAULT_ACCENT,
    position: typeof raw?.position === 'number' ? raw.position : 0,
    accounts: normalizeAccounts(raw?.accounts || []),
  }
}

function unwrap(result) {
  if (!result) return {}
  if (Object.prototype.hasOwnProperty.call(result, 'data')) {
    if (result.status && typeof result.status === 'string') {
      return result.data ?? {}
    }
    return result.data
  }
  return result
}

function cloneGroups(groups) {
  return groups.map((group) => ({
    ...group,
    accounts: normalizeAccounts(group.accounts),
  }))
}

export function useAccountGroups(options = {}) {
  const groups = ref([])
  const activeGroupId = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const scope = options.userId ? String(options.userId) : ''
  const offlineMode = ref(false)

  const storageKey = scope ? `${STORAGE_BASE_KEY}.${scope}` : STORAGE_BASE_KEY

  const readFromStorage = () => {
    if (typeof localStorage === 'undefined') return null
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) return null
      const parsed = JSON.parse(raw)
      if (!parsed || typeof parsed !== 'object') return null
      const storedGroups = Array.isArray(parsed.groups) ? parsed.groups.map(normalizeGroup) : []
      const storedActive = parsed.activeGroupId ? String(parsed.activeGroupId) : null
      return { groups: storedGroups, activeGroupId: storedActive }
    } catch (err) {
      console.warn('Failed to read account groups from storage:', err)
      return null
    }
  }

  const persistToStorage = () => {
    if (typeof localStorage === 'undefined') return
    try {
      const payload = {
        groups: cloneGroups(groups.value),
        activeGroupId: activeGroupId.value,
      }
      localStorage.setItem(storageKey, JSON.stringify(payload))
    } catch (err) {
      console.warn('Failed to persist account groups to storage:', err)
    }
  }

  const scopedPayload = (payload = {}) => ({
    ...(payload || {}),
    ...(scope ? { user_id: scope } : {}),
  })

  const syncFromListResponse = (result) => {
    const payload = unwrap(result)
    if (Array.isArray(payload?.groups)) {
      groups.value = payload.groups.map(normalizeGroup)
    }
    if (payload?.active_group_id) {
      activeGroupId.value = String(payload.active_group_id)
    } else if (!activeGroupId.value && groups.value.length) {
      activeGroupId.value = groups.value[0].id
    }
    offlineMode.value = false
    persistToStorage()
  }

  const syncFromGroupResponse = (result) => {
    const payload = unwrap(result)
    if (payload?.active_group_id) {
      activeGroupId.value = String(payload.active_group_id)
    }
    if (!payload?.group) return
    const normalized = normalizeGroup(payload.group)
    const idx = groups.value.findIndex((group) => group.id === normalized.id)
    if (idx === -1) {
      groups.value.push(normalized)
    } else {
      groups.value.splice(idx, 1, normalized)
    }
  }

  const hydrateFromStorage = () => {
    const stored = readFromStorage()
    if (!stored || !stored.groups?.length) return false
    groups.value = stored.groups
    activeGroupId.value = stored.activeGroupId || stored.groups[0]?.id || null
    return true
  }

  const ensureFallbackGroup = () => {
    if (groups.value.length) return
    const fallback = normalizeGroup({ id: generateId() })
    groups.value = [fallback]
    activeGroupId.value = fallback.id
  }

  const handleError = (err, rollback) => {
    error.value = err
    if (typeof console !== 'undefined') {
      console.error('Account group request failed:', err)
    }
    const isNetworkIssue = !err || !err.response
    if (isNetworkIssue) {
      offlineMode.value = true
      if (!groups.value.length) {
        if (!hydrateFromStorage()) {
          ensureFallbackGroup()
        }
      }
      persistToStorage()
      return
    }
    if (typeof rollback === 'function') {
      rollback()
    }
  }

  const fetchGroups = async () => {
    loading.value = true
    try {
      const response = await api.fetchAccountGroups(scopedPayload())
      syncFromListResponse(response)
    } catch (err) {
      handleError(err)
      if (!groups.value.length) {
        if (!hydrateFromStorage()) {
          ensureFallbackGroup()
        }
      }
    } finally {
      loading.value = false
    }
  }

  const createGroup = (name = DEFAULT_GROUP_NAME, accent = DEFAULT_ACCENT) => {
    const id = generateId()
    const previousActive = activeGroupId.value
    const optimistic = {
      id,
      name,
      accent,
      position: groups.value.length,
      accounts: [],
    }
    groups.value = [...groups.value, optimistic]
    activeGroupId.value = id
    persistToStorage()

    if (offlineMode.value) {
      persistToStorage()
      return id
    }

    api
      .createAccountGroup(scopedPayload({ id, name, accent }))
      .then((response) => {
        syncFromGroupResponse(response)
        persistToStorage()
      })
      .catch((err) => {
        handleError(err, () => {
          groups.value = groups.value.filter((group) => group.id !== id)
          if (!groups.value.length) {
            ensureFallbackGroup()
          } else if (previousActive) {
            activeGroupId.value = previousActive
          } else {
            activeGroupId.value = groups.value[0]?.id || null
          }
          persistToStorage()
        })
      })

    return id
  }

  const updateGroup = (groupId, updates = {}) => {
    const group = groups.value.find((item) => item.id === groupId)
    if (!group) return
    const previous = { name: group.name, accent: group.accent }
    if (Object.prototype.hasOwnProperty.call(updates, 'name')) {
      group.name = updates.name || DEFAULT_GROUP_NAME
    }
    if (Object.prototype.hasOwnProperty.call(updates, 'accent')) {
      group.accent = updates.accent || DEFAULT_ACCENT
    }
    persistToStorage()

    if (offlineMode.value) return

    api
      .updateAccountGroup(groupId, scopedPayload(updates))
      .then((response) => {
        syncFromGroupResponse(response)
        persistToStorage()
      })
      .catch((err) => {
        handleError(err, () => {
          group.name = previous.name
          group.accent = previous.accent
          persistToStorage()
        })
      })
  }

  const removeGroup = (groupId) => {
    const previousGroups = cloneGroups(groups.value)
    const previousActive = activeGroupId.value
    groups.value = groups.value.filter((group) => group.id !== groupId)
    if (!groups.value.length) {
      ensureFallbackGroup()
    } else if (!groups.value.some((group) => group.id === activeGroupId.value)) {
      activeGroupId.value = groups.value[0].id
    }
    persistToStorage()

    if (offlineMode.value) return

    api
      .deleteAccountGroup(groupId, scopedPayload())
      .then((response) => {
        syncFromListResponse(response)
        persistToStorage()
      })
      .catch((err) => {
        handleError(err, () => {
          groups.value = previousGroups
          activeGroupId.value = previousActive
          persistToStorage()
        })
      })
  }

  const reorderGroups = (orderedGroups) => {
    const targetOrder = Array.isArray(orderedGroups)
      ? orderedGroups.map((entry) => (typeof entry === 'string' ? entry : entry.id))
      : []
    if (!targetOrder.length) return
    const previous = cloneGroups(groups.value)
    const ordered = targetOrder
      .map((id) => groups.value.find((group) => group.id === id))
      .filter(Boolean)
    if (ordered.length !== groups.value.length) return
    groups.value = ordered.map((group, index) => ({ ...group, position: index }))
    persistToStorage()

    if (offlineMode.value) return

    api
      .reorderAccountGroups(scopedPayload({ group_ids: targetOrder }))
      .then((response) => {
        syncFromListResponse(response)
        persistToStorage()
      })
      .catch((err) => {
        handleError(err, () => {
          groups.value = previous
          persistToStorage()
        })
      })
  }

  const setActiveGroup = (groupId) => {
    if (!groupId || !groups.value.some((group) => group.id === groupId)) return
    const previous = activeGroupId.value
    activeGroupId.value = groupId
    persistToStorage()

    if (offlineMode.value) return

    api
      .setActiveAccountGroup(scopedPayload({ group_id: groupId }))
      .then((response) => {
        syncFromListResponse(response)
        persistToStorage()
      })
      .catch((err) => {
        handleError(err, () => {
          activeGroupId.value = previous
          persistToStorage()
        })
      })
  }

  const addAccountToGroup = (groupId, account) => {
    const group = groups.value.find((item) => item.id === groupId)
    if (!group) return false
    if (group.accounts.length >= MAX_ACCOUNTS_PER_GROUP) return false
    const normalized = normalizeAccount(account)
    if (!normalized) return false
    if (group.accounts.some((existing) => existing.id === normalized.id)) return false

    const previous = group.accounts.slice()
    group.accounts.push(normalized)
    persistToStorage()

    if (!offlineMode.value) {
      api
        .addAccountToGroup(groupId, scopedPayload({ account_id: normalized.account_id }))
        .then((response) => {
          syncFromGroupResponse(response)
          persistToStorage()
        })
        .catch((err) => {
          handleError(err, () => {
            group.accounts.splice(0, group.accounts.length, ...previous)
            persistToStorage()
          })
        })
    }
    return true
  }

  const removeAccountFromGroup = (groupId, accountId) => {
    const group = groups.value.find((item) => item.id === groupId)
    if (!group) return false
    const resolvedId = resolveAccountId(accountId)
    const index = group.accounts.findIndex((acct) => resolveAccountId(acct) === resolvedId)
    if (index === -1) return false
    const previous = group.accounts.slice()
    group.accounts.splice(index, 1)
    persistToStorage()

    if (!offlineMode.value) {
      api
        .removeAccountFromGroup(groupId, resolvedId, scopedPayload())
        .then((response) => {
          syncFromGroupResponse(response)
          persistToStorage()
        })
        .catch((err) => {
          handleError(err, () => {
            group.accounts.splice(0, group.accounts.length, ...previous)
            persistToStorage()
          })
        })
    }
    return true
  }

  const syncGroupAccounts = (groupId, accounts) => {
    const group = groups.value.find((item) => item.id === groupId)
    if (!group) return
    const normalized = normalizeAccounts(accounts)
    const previous = group.accounts.slice()
    group.accounts.splice(0, group.accounts.length, ...normalized)
    persistToStorage()

    if (!offlineMode.value) {
      api
        .reorderGroupAccounts(
          groupId,
          scopedPayload({ account_ids: normalized.map((acct) => acct.account_id) }),
        )
        .then((response) => {
          syncFromGroupResponse(response)
          persistToStorage()
        })
        .catch((err) => {
          handleError(err, () => {
            group.accounts.splice(0, group.accounts.length, ...previous)
            persistToStorage()
          })
        })
    }
  }

  fetchGroups()

  return {
    groups,
    activeGroupId,
    loading,
    error,
    offlineMode,
    fetchGroups,
    createGroup,
    updateGroup,
    removeGroup,
    reorderGroups,
    setActiveGroup,
    addAccountToGroup,
    removeAccountFromGroup,
    syncGroupAccounts,
  }
}
