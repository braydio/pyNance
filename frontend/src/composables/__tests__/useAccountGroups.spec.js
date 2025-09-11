import { beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { useAccountGroups } from '../useAccountGroups.js'

const STORAGE_KEY = 'accountGroups'

beforeEach(() => {
  const store = {}
  vi.stubGlobal('localStorage', {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => {
      store[k] = String(v)
    },
    removeItem: (k) => {
      delete store[k]
    },
    clear: () => {
      Object.keys(store).forEach((k) => delete store[k])
    },
  })
  localStorage.clear()
})

describe('useAccountGroups', () => {
  it('loads groups from localStorage', () => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        groups: [{ id: 'stored', name: 'Stored', accounts: [] }],
        activeGroupId: 'stored',
      }),
    )
    const { groups, activeGroupId } = useAccountGroups()
    expect(groups.value[0].id).toBe('stored')
    expect(activeGroupId.value).toBe('stored')
  })

  it('persists group changes', async () => {
    const { groups } = useAccountGroups()
    groups.value[0].name = 'Updated'
    await nextTick()
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY))
    expect(stored.groups[0].name).toBe('Updated')
  })

  it('adds and removes groups while maintaining active id', async () => {
    const { groups, activeGroupId, addGroup, setActiveGroup, removeGroup } = useAccountGroups()
    const firstId = groups.value[0].id
    const newId = addGroup('New')
    expect(activeGroupId.value).toBe(newId)
    setActiveGroup(firstId)
    expect(activeGroupId.value).toBe(firstId)
    removeGroup(firstId)
    await nextTick()
    expect(groups.value.length).toBe(1)
    expect(activeGroupId.value).toBe(groups.value[0].id)
  })

  it('reorders groups and persists deletions', async () => {
    const { groups, reorderGroups, removeGroup } = useAccountGroups()
    groups.value.push({ id: 'b', name: 'B', accounts: [] })
    reorderGroups([...groups.value].reverse())
    await nextTick()
    let stored = JSON.parse(localStorage.getItem(STORAGE_KEY))
    expect(stored.groups[0].id).toBe('b')
    removeGroup('b')
    await nextTick()
    stored = JSON.parse(localStorage.getItem(STORAGE_KEY))
    expect(stored.groups.some((g) => g.id === 'b')).toBe(false)
  })

  it('prevents duplicate accounts and removes accounts', async () => {
    const { addAccountToGroup, removeAccountFromGroup, groups } = useAccountGroups()
    const id = groups.value[0].id
    const acc = { id: 'a1' }
    expect(addAccountToGroup(id, acc)).toBe(true)
    expect(addAccountToGroup(id, acc)).toBe(false)
    removeAccountFromGroup(id, 'a1')
    await nextTick()
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY))
    expect(groups.value[0].accounts.length).toBe(0)
    expect(stored.groups[0].accounts.length).toBe(0)
  })

  it('enforces a maximum of five accounts per group', () => {
    const { addAccountToGroup, groups } = useAccountGroups()
    const id = groups.value[0].id
    for (let i = 0; i < 5; i += 1) {
      expect(addAccountToGroup(id, `acc-${i}`)).toBe(true)
    }
    expect(addAccountToGroup(id, 'acc-5')).toBe(false)
    expect(groups.value[0].accounts.length).toBe(5)
  })
})
