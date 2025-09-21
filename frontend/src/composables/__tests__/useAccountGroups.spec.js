import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

const DEFAULT_ACCENT = 'var(--color-accent-cyan)'

vi.mock('@/services/api', () => {
  const backendState = {
    groups: [],
    active_group_id: 'group-1',
  }

  const snapshot = () => ({
    status: 'success',
    data: {
      groups: backendState.groups.map((group, index) => ({
        ...group,
        position: index,
        accounts: group.accounts.map((acct) => ({ ...acct })),
      })),
      active_group_id: backendState.active_group_id,
    },
  })

  const ensureGroup = (id) => {
    const group = backendState.groups.find((item) => item.id === id)
    if (!group) {
      throw new Error(`Group ${id} not found`)
    }
    return group
  }

  const api = {
    __state: backendState,
    __reset: () => {
      backendState.groups = [
        {
          id: 'group-1',
          name: 'Group',
          accent: DEFAULT_ACCENT,
          position: 0,
          accounts: [],
        },
      ]
      backendState.active_group_id = 'group-1'
      Object.values(api).forEach((fn) => {
        if (typeof fn?.mockClear === 'function') {
          fn.mockClear()
        }
      })
    },
    fetchAccountGroups: vi.fn(async () => snapshot()),
    createAccountGroup: vi.fn(async ({ id, name, accent }) => {
      const groupId = id || `group-${Date.now()}`
      backendState.groups.push({
        id: groupId,
        name: name || 'Group',
        accent: accent || DEFAULT_ACCENT,
        position: backendState.groups.length,
        accounts: [],
      })
      backendState.active_group_id = groupId
      return {
        status: 'success',
        data: {
          group: snapshot().data.groups.find((group) => group.id === groupId),
          active_group_id: backendState.active_group_id,
        },
      }
    }),
    updateAccountGroup: vi.fn(async (id, payload = {}) => {
      const group = ensureGroup(id)
      if (payload.name) group.name = payload.name
      if (payload.accent) group.accent = payload.accent
      return {
        status: 'success',
        data: {
          group: snapshot().data.groups.find((item) => item.id === id),
        },
      }
    }),
    deleteAccountGroup: vi.fn(async (id) => {
      backendState.groups = backendState.groups.filter((group) => group.id !== id)
      if (!backendState.groups.length) {
        backendState.groups = [
          {
            id: 'group-1',
            name: 'Group',
            accent: DEFAULT_ACCENT,
            position: 0,
            accounts: [],
          },
        ]
      }
      if (!backendState.groups.some((group) => group.id === backendState.active_group_id)) {
        backendState.active_group_id = backendState.groups[0].id
      }
      return snapshot()
    }),
    reorderAccountGroups: vi.fn(async ({ group_ids }) => {
      const ordered = group_ids
        .map((id) => backendState.groups.find((group) => group.id === id))
        .filter(Boolean)
      if (ordered.length === backendState.groups.length) {
        backendState.groups = ordered
      }
      return snapshot()
    }),
    setActiveAccountGroup: vi.fn(async ({ group_id }) => {
      backendState.active_group_id = group_id
      return {
        status: 'success',
        data: { active_group_id: backendState.active_group_id },
      }
    }),
    addAccountToGroup: vi.fn(async (groupId, { account_id }) => {
      const group = ensureGroup(groupId)
      if (!group.accounts.some((acct) => acct.id === account_id)) {
        group.accounts.push({
          id: account_id,
          account_id,
          name: `Account ${account_id}`,
          adjusted_balance: 0,
        })
      }
      return {
        status: 'success',
        data: {
          group: snapshot().data.groups.find((item) => item.id === groupId),
        },
      }
    }),
    removeAccountFromGroup: vi.fn(async (groupId, accountId) => {
      const group = ensureGroup(groupId)
      group.accounts = group.accounts.filter((acct) => acct.id !== accountId)
      return {
        status: 'success',
        data: {
          group: snapshot().data.groups.find((item) => item.id === groupId),
        },
      }
    }),
    reorderGroupAccounts: vi.fn(async (groupId, { account_ids }) => {
      const group = ensureGroup(groupId)
      group.accounts = account_ids
        .map((id) => group.accounts.find((acct) => acct.id === id))
        .filter(Boolean)
      return {
        status: 'success',
        data: {
          group: snapshot().data.groups.find((item) => item.id === groupId),
        },
      }
    }),
  }

  api.__reset()
  return { default: api }
})

import api from '@/services/api'
import { useAccountGroups } from '../useAccountGroups.js'

const flush = async () => {
  await Promise.resolve()
  await nextTick()
  await Promise.resolve()
}

describe('useAccountGroups', () => {
  beforeEach(() => {
    api.__reset()
  })

  it('loads groups from the API', async () => {
    const { groups, activeGroupId } = useAccountGroups()
    await flush()
    expect(groups.value).toHaveLength(1)
    expect(activeGroupId.value).toBe('group-1')
  })

  it('creates a group and persists it across reloads', async () => {
    const first = useAccountGroups()
    await flush()
    const newId = first.createGroup('Savings')
    await flush()
    expect(first.groups.value.some((group) => group.id === newId)).toBe(true)

    const reload = useAccountGroups()
    await flush()
    expect(reload.groups.value.some((group) => group.id === newId)).toBe(true)
    expect(reload.activeGroupId.value).toBe(newId)
  })

  it('adds accounts without duplicates and persists removal', async () => {
    const store = useAccountGroups()
    await flush()
    const groupId = store.groups.value[0].id

    expect(store.addAccountToGroup(groupId, { id: 'acc-1', name: 'Checking' })).toBe(true)
    await flush()
    expect(store.addAccountToGroup(groupId, { id: 'acc-1', name: 'Checking' })).toBe(false)
    expect(store.groups.value[0].accounts).toHaveLength(1)

    store.removeAccountFromGroup(groupId, 'acc-1')
    await flush()
    expect(store.groups.value[0].accounts).toHaveLength(0)

    const reload = useAccountGroups()
    await flush()
    expect(reload.groups.value[0].accounts).toHaveLength(0)
  })

  it('updates active group selection via the API', async () => {
    const store = useAccountGroups()
    await flush()
    const newId = store.createGroup('Travel')
    await flush()
    store.setActiveGroup(newId)
    await flush()
    expect(store.activeGroupId.value).toBe(newId)

    const reload = useAccountGroups()
    await flush()
    expect(reload.activeGroupId.value).toBe(newId)
  })
})
