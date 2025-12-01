// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick, watch } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

function ensureMockStorage() {
  if (typeof localStorage !== 'undefined' && typeof localStorage.clear === 'function') {
    return
  }
  let store = {}
  const storage = {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, val) => {
      store[key] = String(val)
    },
    removeItem: (key) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
  Object.defineProperty(globalThis, 'localStorage', { value: storage, writable: true })
}

ensureMockStorage()

const sampleAccounts = [
  { id: 'acc-1', name: 'Account 1', adjusted_balance: 1 },
  { id: 'acc-2', name: 'Account 2', adjusted_balance: 2 },
]

const accountsRef = ref(sampleAccounts.map((acct) => ({ ...acct })))
const addAccountToGroupMock = vi.fn()
const removeAccountFromGroupMock = vi.fn()

vi.mock('@/composables/useTopAccounts', () => {
  const fetchAccounts = vi.fn()
  return {
    useTopAccounts: () => {
      fetchAccounts()
      return { fetchAccounts, accounts: accountsRef, allVisibleAccounts: accountsRef }
    },
  }
})

vi.mock('@/composables/useAccountGroups', () => {
  const STORAGE_KEY = 'accountGroups'
  return {
    useAccountGroups() {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
      const groups = ref(
        stored?.groups?.map((group) => ({
          ...group,
          accounts: Array.isArray(group.accounts)
            ? group.accounts.map((acct) => ({ ...acct }))
            : [],
        })) || [{ id: 'group-1', name: 'Group', accounts: [] }],
      )
      const activeGroupId = ref(stored?.activeGroupId || groups.value[0].id)

      function persist() {
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ groups: groups.value, activeGroupId: activeGroupId.value }),
        )
      }

      function setActiveGroup(id) {
        if (groups.value.some((group) => group.id === id)) {
          activeGroupId.value = id
        }
      }

      const removeGroup = vi.fn((id) => {
        const idx = groups.value.findIndex((group) => group.id === id)
        if (idx !== -1) {
          groups.value.splice(idx, 1)
          if (!groups.value.length) {
            groups.value.push({ id: 'group-1', name: 'Group', accounts: [] })
          }
          if (!groups.value.some((group) => group.id === activeGroupId.value)) {
            activeGroupId.value = groups.value[0].id
          }
        }
      })

      const createGroup = (name = 'Group') => {
        const id = crypto.randomUUID ? crypto.randomUUID() : `group-${Date.now()}`
        groups.value.push({ id, name, accounts: [] })
        setActiveGroup(id)
        return id
      }

      const updateGroup = (id, updates = {}) => {
        const target = groups.value.find((group) => group.id === id)
        if (!target) return
        if (Object.prototype.hasOwnProperty.call(updates, 'name')) {
          target.name = updates.name || target.name
        }
        if (Object.prototype.hasOwnProperty.call(updates, 'accent')) {
          target.accent = updates.accent
        }
      }

      const reorderGroups = (order) => {
        const ordered = order.map((entry) => (typeof entry === 'string' ? entry : entry.id))
        const next = ordered
          .map((id) => groups.value.find((group) => group.id === id))
          .filter(Boolean)
        if (next.length === groups.value.length) {
          groups.value = [...next]
        }
      }

      const addAccountToGroup = (groupId, account) => {
        addAccountToGroupMock(groupId, account)
        const target = groups.value.find((group) => group.id === groupId)
        if (!target || target.accounts.length >= 5) {
          return false
        }
        const accountId = account?.id ?? account?.account_id ?? account
        if (!accountId) return false
        if (target.accounts.some((acct) => acct.id === accountId)) {
          return false
        }
        target.accounts.push({ ...account, id: accountId })
        persist()
        return true
      }

      const removeAccountFromGroup = (groupId, accountId) => {
        removeAccountFromGroupMock(groupId, accountId)
        const target = groups.value.find((group) => group.id === groupId)
        if (!target) return false
        const idx = target.accounts.findIndex((acct) => acct.id === accountId)
        if (idx === -1) return false
        target.accounts.splice(idx, 1)
        persist()
        return true
      }

      const syncGroupAccounts = (groupId, accounts) => {
        const target = groups.value.find((group) => group.id === groupId)
        if (!target) return
        target.accounts = [...accounts]
        persist()
      }

      watch([groups, activeGroupId], persist, { deep: true })
      persist()

      return {
        groups,
        activeGroupId,
        createGroup,
        updateGroup,
        removeGroup,
        reorderGroups,
        setActiveGroup,
        addAccountToGroup,
        removeAccountFromGroup,
        syncGroupAccounts,
      }
    },
  }
})

// Stub fetchRecentTransactions to avoid network calls in jsdom
vi.mock('@/api/accounts', () => ({
  fetchRecentTransactions: vi.fn(async () => ({ data: { transactions: [] } })),
}))

beforeEach(() => {
  ensureMockStorage()
  localStorage.clear()
  accountsRef.value = sampleAccounts.map((acct) => ({ ...acct }))
  addAccountToGroupMock.mockReset()
  removeAccountFromGroupMock.mockReset()
})

describe('TopAccountSnapshot editing behaviour', () => {
  it('allows adding and removing accounts while editing groups', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          {
            id: 'group-1',
            name: 'Group',
            accounts: [sampleAccounts[0]],
          },
        ],
        activeGroupId: 'group-1',
      }),
    )

    const wrapper = mount(TopAccountSnapshot, {
      props: { isEditingGroups: true },
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()

    const accountRows = () =>
      wrapper
        .findAll('.bs-account-container')
        .filter((node) => !node.classes().includes('bs-add-account'))

    expect(accountRows()).toHaveLength(1)

    const deleteButtons = wrapper.findAll('.bs-account-delete')
    expect(deleteButtons.length).toBeGreaterThan(0)
    await deleteButtons[0].trigger('click')
    await nextTick()

    expect(accountRows()).toHaveLength(0)
    expect(removeAccountFromGroupMock).toHaveBeenCalledWith('group-1', 'acc-1')

    const addTrigger = wrapper.find('.bs-add-placeholder')
    expect(addTrigger.exists()).toBe(true)
    await addTrigger.trigger('click')
    await nextTick()

    expect(wrapper.find('.bs-add-select').exists()).toBe(true)

    const confirmStub = vi.fn(() => {
      const nextAccount = { ...sampleAccounts[1] }
      addAccountToGroupMock('group-1', nextAccount)
      wrapper.vm.showAccountSelector = false
      wrapper.vm.selectedAccountId = ''
    })

    wrapper.vm.$.setupState.confirmAddAccount = confirmStub
    wrapper.vm.selectedAccountId = 'acc-2'
    await wrapper.vm.$.setupState.confirmAddAccount()
    await nextTick()

    expect(confirmStub).toHaveBeenCalled()
    expect(addAccountToGroupMock).toHaveBeenCalledWith(
      'group-1',
      expect.objectContaining({ id: 'acc-2' }),
    )
    expect(wrapper.vm.showAccountSelector).toBe(false)
    expect(wrapper.vm.selectedAccountId).toBe('')
  })
})
