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
        const idx = group.accounts.findIndex(
          (a) => a.id === accountId || a.account_id === accountId,
        )
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
      groups: [{ id: 'group-1', name: 'Group', accounts: sampleAccounts }],
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
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
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

  it('collapses the group dropdown after selecting a group', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
    await nextTick()
    const firstGroupId = wrapper.vm.activeGroupId?.value || wrapper.vm.groups?.value?.[0]?.id
    wrapper.vm.showGroupMenu = true
    wrapper.vm.selectGroup(firstGroupId)
    await nextTick()
    expect(wrapper.vm.showGroupMenu).toBe(false)
  })

  it('styles credit balances as negative and non-credit balances by sign', async () => {
    const customAccounts = [
      {
        id: 'credit-pos',
        account_id: 'credit-pos',
        name: 'Credit Positive',
        adjusted_balance: 120,
        subtype: 'credit card',
      },
      {
        id: 'credit-neg',
        account_id: 'credit-neg',
        name: 'Credit Negative',
        adjusted_balance: -55,
        type: 'credit',
      },
      {
        id: 'debit-pos',
        account_id: 'debit-pos',
        name: 'Checking Positive',
        adjusted_balance: 45,
        type: 'depository',
      },
      {
        id: 'debit-neg',
        account_id: 'debit-neg',
        name: 'Savings Negative',
        adjusted_balance: -10,
        subtype: 'savings',
      },
    ]
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'group-1', name: 'Group', accounts: customAccounts }],
        activeGroupId: 'group-1',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
    await nextTick()
    const amounts = wrapper.findAll('.bs-account-container .bs-amount')
    expect(amounts).toHaveLength(4)
    expect(amounts[0].classes()).toContain('bs-balance-neg')
    expect(amounts[1].classes()).toContain('bs-balance-neg')
    expect(amounts[2].classes()).toContain('bs-balance-pos')
    expect(amounts[3].classes()).toContain('bs-balance-neg')
  })

  it('shows utilization only for credit accounts with a limit', async () => {
    const customAccounts = [
      {
        id: 'credit-limit',
        account_id: 'credit-limit',
        name: 'Credit Limit',
        adjusted_balance: -2100,
        subtype: 'credit card',
        limit: 6500,
      },
      {
        id: 'credit-no-limit',
        account_id: 'credit-no-limit',
        name: 'Credit No Limit',
        adjusted_balance: -800,
        type: 'credit',
      },
      {
        id: 'debit-limit',
        account_id: 'debit-limit',
        name: 'Checking',
        adjusted_balance: 500,
        type: 'depository',
        credit_limit: 1500,
      },
    ]
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'group-1', name: 'Group', accounts: customAccounts }],
        activeGroupId: 'group-1',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: sparklineStub } },
    })
    await nextTick()

    const utilizationBlocks = wrapper.findAll('.bs-utilization')
    expect(utilizationBlocks).toHaveLength(1)
    expect(utilizationBlocks[0].text()).toContain('Utilization')
    expect(utilizationBlocks[0].text()).toContain('$2,100.00')
    expect(utilizationBlocks[0].text()).toContain('$6,500.00')
    expect(utilizationBlocks[0].text()).toContain('32%')

    const creditNoLimitRow = wrapper
      .findAll('.bs-account-container')
      .find((row) => row.text().includes('Credit No Limit'))
    expect(creditNoLimitRow?.find('.bs-utilization').exists()).toBe(false)

    const debitLimitRow = wrapper
      .findAll('.bs-account-container')
      .find((row) => row.text().includes('Checking'))
    expect(debitLimitRow?.find('.bs-utilization').exists()).toBe(false)
  })
})
