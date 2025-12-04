// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

// Basic localStorage shim for the test environment
function ensureMockStorage() {
  if (typeof localStorage !== 'undefined' && typeof localStorage.clear === 'function') return
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

// Sample data (hoisted for use inside mocks)
const sampleAccounts = vi.hoisted(() => [
  { id: 'acc-1', account_id: 'acc-1', name: 'Account 1', adjusted_balance: 1, mask: '1111' },
  { id: 'acc-2', account_id: 'acc-2', name: 'Account 2', adjusted_balance: 2, mask: '2222' },
])

// --- Composable Mocks ---
vi.mock('@/composables/useTopAccounts', () => {
  const fetchAccounts = vi.fn()
  const accounts = ref([...sampleAccounts])
  const allVisibleAccounts = ref(accounts.value)
  return {
    useTopAccounts: () => {
      fetchAccounts()
      return { fetchAccounts, accounts, allVisibleAccounts }
    },
  }
})

vi.mock('@/composables/useAccountGroups', () => {
  const STORAGE_KEY = 'accountGroups'
  return {
    useAccountGroups() {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
      const groups = ref(stored?.groups || [{ id: 'group-1', name: 'Group', accounts: [] }])
      const activeGroupId = ref(stored?.activeGroupId || groups.value[0].id)

      function persist() {
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ groups: groups.value, activeGroupId: activeGroupId.value }),
        )
      }

      function setActiveGroup(id) {
        if (groups.value.some((g) => g.id === id)) {
          activeGroupId.value = id
          persist()
        }
      }

      function createGroup(name = 'Group') {
        const id = crypto.randomUUID ? crypto.randomUUID() : `group-${Date.now()}`
        groups.value.push({ id, name, accounts: [] })
        setActiveGroup(id)
        persist()
        return id
      }

      function updateGroup(id, updates = {}) {
        const group = groups.value.find((item) => item.id === id)
        if (!group) return
        if (Object.prototype.hasOwnProperty.call(updates, 'name')) {
          group.name = updates.name || group.name
        }
        persist()
      }

      function removeGroup(id) {
        const idx = groups.value.findIndex((g) => g.id === id)
        if (idx !== -1) {
          groups.value.splice(idx, 1)
          if (!groups.value.length) {
            groups.value.push({ id: 'group-1', name: 'Group', accounts: [] })
          }
          if (!groups.value.some((g) => g.id === activeGroupId.value)) {
            activeGroupId.value = groups.value[0].id
          }
          persist()
        }
      }

      function addAccountToGroup(groupId, account) {
        const group = groups.value.find((g) => g.id === groupId)
        if (group && group.accounts.length < 5) {
          group.accounts.push(account)
          persist()
        }
      }

      function removeAccountFromGroup(groupId, accountId) {
        const group = groups.value.find((g) => g.id === groupId)
        if (!group) return
        const idx = group.accounts.findIndex((a) => a.id === accountId || a.account_id === accountId)
        if (idx !== -1) {
          group.accounts.splice(idx, 1)
          persist()
        }
      }

      function syncGroupAccounts(groupId, accounts) {
        const group = groups.value.find((g) => g.id === groupId)
        if (group) {
          group.accounts = accounts
          persist()
        }
      }

      function reorderGroups(nextGroups) {
        groups.value = [...nextGroups]
        persist()
      }

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
        offlineMode: ref(false),
      }
    },
  }
})

vi.mock('@/api/accounts', () => ({
  fetchRecentTransactions: vi.fn(async () => ({ transactions: [] })),
}))

const sparklineStub = {
  name: 'AccountSparkline',
  template: '<div class=\"spark\"></div>',
}

beforeEach(() => {
  localStorage.clear()
  localStorage.setItem(
    'accountGroups',
    JSON.stringify({
      groups: [
        { id: 'group-1', name: 'Group', accounts: sampleAccounts },
      ],
      activeGroupId: 'group-1',
    }),
  )
})

describe('TopAccountSnapshot', () => {
  it('renders account rows with individual balances', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
    await nextTick()
    const rows = wrapper.findAll('.bs-account-container .bs-row')
    expect(rows.length).toBeGreaterThanOrEqual(2)
    expect(rows[0].text()).toContain('Account 1')
    expect(rows[0].text()).toMatch(/\$1\.00/)
  })

  it('shows total balance pill for visible accounts', async () => {
    const wrapper = mount(TopAccountSnapshot, { global: { stubs: { AccountSparkline: sparklineStub } } })
    await nextTick()
    expect(wrapper.find('.bs-total-value').text()).toContain('$3.00')
  })

  it('toggles edit mode from the group menu and emits update', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
    const switchBtn = wrapper.find('button.bs-group-btn')
    await switchBtn.trigger('click')
    const editBtn = wrapper.find('.bs-group-item.bs-group-action')
    expect(editBtn.exists()).toBe(true)
    await editBtn.trigger('click')
    await nextTick()
    expect(wrapper.find('.bank-statement-list').classes()).toContain('bs-editing')
    expect(wrapper.emitted('update:isEditingGroups')?.[0]).toEqual([true])
  })

})
