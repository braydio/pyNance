// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, watch, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

const STORAGE_KEY = 'accountGroups'

// Sample accounts used for localStorage-backed groups
const sampleAccounts = [
  { id: 'acc-1', name: 'Account 1', adjusted_balance: 1 },
  { id: 'acc-2', name: 'Account 2', adjusted_balance: 2 },
]

// --- Composable Mocks ---

// Mock useTopAccounts to mimic a generic account fetch
vi.mock('@/composables/useTopAccounts', () => {
  const fetchAccounts = vi.fn()
  return {
    useTopAccounts: () => {
      fetchAccounts()
      return { fetchAccounts }
    },
  }
})

// Mock useAccountGroups with basic localStorage persistence
vi.mock('@/composables/useAccountGroups', () => {
  const STORAGE_KEY = 'accountGroups'
  return {
    useAccountGroups() {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
      const groups = ref(stored?.groups || [{ id: 'group-1', name: 'Group', accounts: [] }])
      const activeGroupId = ref(stored?.activeGroupId || groups.value[0].id)
      const addAccountToGroup = (groupId, account) => {
        const group = groups.value.find((g) => g.id === groupId)
        if (group) group.accounts.push(account)
      }
      const removeAccountFromGroup = (groupId, accountId) => {
        const group = groups.value.find((g) => g.id === groupId)
        if (!group) return
        group.accounts = group.accounts.filter(
          (a) => a.id !== accountId && a.account_id !== accountId,
        )
      }

      watch(
        [groups, activeGroupId],
        () => {
          localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({ groups: groups.value, activeGroupId: activeGroupId.value }),
          )
        },
        { deep: true },
      )

      return { groups, activeGroupId, addAccountToGroup, removeAccountFromGroup }
    },
  }
})

vi.mock('@/composables/useAccountSelector', () => {
  return {
    useAccountSelector() {
      return {
        availableAccounts: ref([]),
        selectedAccountIds: ref([]),
        selectedAccounts: ref([]),
        loading: ref(false),
        error: ref(null),
        toggleAccount: vi.fn(),
        selectAll: vi.fn(),
        deselectAll: vi.fn(),
        selectAccountsByType: vi.fn(),
        fetchAccounts: vi.fn(),
      }
    },
  }
})

beforeEach(() => {
  localStorage.clear()
})

describe('TopAccountSnapshot', () => {
  it('creates default group, adds new group, and saves edited name', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()

    const names = wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(names).toContain('Group')

    wrapper.vm.addGroup()
    await nextTick()
    const input = wrapper.find('input.bs-tab')
    expect(input.exists()).toBe(true)
    await input.setValue('My Group')
    await input.trigger('blur')
    await nextTick()
    const updated = wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(updated).toContain('My Group')
  })

  it('updates group order when accounts are reordered', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'group-1', name: 'Group', accounts: sampleAccounts }],
        activeGroupId: 'group-1',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    const firstBefore = wrapper.findAll('.bs-name')[0].text()
    wrapper.vm.groups[0].accounts.reverse()
    await nextTick()
    const firstAfter = wrapper.findAll('.bs-name')[0].text()
    expect(firstAfter).not.toBe(firstBefore)
  })

  it('restores groups from localStorage', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'saved', name: 'Saved', accounts: [] }],
        activeGroupId: 'saved',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    const names = wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(names).toContain('Saved')
  })

  it('derives accent color from group data or defaults', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          { id: 'colored', name: 'Colored', accounts: [], accent: 'var(--color-accent-red)' },
          { id: 'group-1', name: 'Group', accounts: [] },
        ],
        activeGroupId: 'colored',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    expect(wrapper.vm.groupAccent).toBe('var(--color-accent-red)')

    wrapper.vm.activeGroupId = 'group-1'
    await nextTick()
    expect(wrapper.vm.groupAccent).toBe('var(--color-accent-cyan)')
  })

  it('shows delete icons and add placeholder in editing mode', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      props: { isEditingGroups: true },
      global: { stubs: { AccountSparkline: true } },
    })
    await nextTick()
    // Add account to trigger delete button
    wrapper.vm.groups[0].accounts.push({ id: 'acc-1', name: 'A1', adjusted_balance: 0 })
    await nextTick()
    expect(wrapper.findAll('.bs-delete-btn').length).toBe(1)
    const addRow = wrapper.find('.bs-add-account')
    expect(addRow.exists()).toBe(true)
    expect(addRow.classes()).not.toContain('bs-add-account-disabled')
  })

  it('disables add account row when group is full', async () => {
    const fullAccounts = Array.from({ length: 5 }, (_, i) => ({
      id: `acc-${i}`,
      adjusted_balance: i,
    }))
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        groups: [{ id: 'group-1', name: 'Group', accounts: fullAccounts }],
        activeGroupId: 'group-1',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      props: { isEditingGroups: true },
      global: { stubs: { AccountSparkline: true } },
    })
    await nextTick()
    const addRow = wrapper.find('.bs-add-account')
    expect(addRow.classes()).toContain('bs-add-account-disabled')
  })
})
