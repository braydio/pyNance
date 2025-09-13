// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, watch, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

// Sample accounts used for localStorage-backed groups
const sampleAccounts = [
  { id: 'acc-1', name: 'Account 1', adjusted_balance: 1 },
  { id: 'acc-2', name: 'Account 2', adjusted_balance: 2 },
]

// --- Composable Mocks ---

// Mock useTopAccounts to mimic a generic account fetch
vi.mock('@/composables/useTopAccounts', () => {
  const fetchAccounts = vi.fn()
  const allVisibleAccounts = ref([
    { id: 'acc-1', name: 'Account 1', adjusted_balance: 1 },
    { id: 'acc-2', name: 'Account 2', adjusted_balance: 2 },
  ])
  return {
    useTopAccounts: () => {
      fetchAccounts()
      return { fetchAccounts, allVisibleAccounts }
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

      function persist() {
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ groups: groups.value, activeGroupId: activeGroupId.value }),
        )
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
        }
      }

      function addAccountToGroup(groupId, account) {
        const group = groups.value.find((g) => g.id === groupId)
        if (group && group.accounts.length < 5) {
          group.accounts.push(account)
        }
      }

      function removeAccountFromGroup(groupId, accountId) {
        const group = groups.value.find((g) => g.id === groupId)
        if (!group) return
        const idx = group.accounts.findIndex((a) => a.id === accountId)
        if (idx !== -1) {
          group.accounts.splice(idx, 1)
        }
      }

      watch([groups, activeGroupId], persist, { deep: true })
      persist()

      return {
        groups,
        activeGroupId,
        removeGroup,
        addAccountToGroup,
        removeAccountFromGroup,
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

  it('renders group names as inputs when editing and saves changes', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          { id: 'a', name: 'A', accounts: [] },
          { id: 'b', name: 'B', accounts: [] },
        ],
        activeGroupId: 'a',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    wrapper.vm.isEditingGroups = true
    await nextTick()

    const inputs = wrapper.findAll('input.bs-tab-input')
    expect(inputs).toHaveLength(2)
    expect(wrapper.findAll('.bs-tab-handle')).toHaveLength(2)
    expect(wrapper.findAll('.bs-tab-delete')).toHaveLength(2)
    await inputs[0].setValue('AA')
    await inputs[0].trigger('blur')
    const stored = JSON.parse(localStorage.getItem('accountGroups'))
    expect(stored.groups[0].name).toBe('AA')
  })

  it('persists group order changes when dragged', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          { id: 'a', name: 'A', accounts: [] },
          { id: 'b', name: 'B', accounts: [] },
        ],
        activeGroupId: 'a',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    wrapper.vm.isEditingGroups = true
    await nextTick()
    wrapper.vm.groups.reverse()
    await nextTick()
    const stored = JSON.parse(localStorage.getItem('accountGroups'))
    expect(stored.groups[0].id).toBe('b')
  })

  it('deletes a group and persists removal', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          { id: 'a', name: 'A', accounts: [] },
          { id: 'b', name: 'B', accounts: [] },
        ],
        activeGroupId: 'a',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    wrapper.vm.isEditingGroups = true
    await nextTick()
    const del = wrapper.findAll('.bs-tab-delete')[0]
    await del.trigger('click')
    await nextTick()
    const stored = JSON.parse(localStorage.getItem('accountGroups'))
    expect(stored.groups).toHaveLength(1)
    expect(stored.groups[0].id).toBe('b')
  })

  it('adds account through placeholder and persists', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'g', name: 'G', accounts: [sampleAccounts[0]] }],
        activeGroupId: 'g',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })
    await nextTick()
    await wrapper.find('.bs-add-placeholder').trigger('click')
    const select = wrapper.find('select.bs-add-select')
    await select.setValue('acc-2')
    await nextTick()
    const stored = JSON.parse(localStorage.getItem('accountGroups'))
    expect(stored.groups[0].accounts).toHaveLength(2)
    expect(stored.groups[0].accounts[1].id).toBe('acc-2')
  })

  it('shows delete icon when editing and removes account', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [{ id: 'g', name: 'G', accounts: [sampleAccounts[0]] }],
        activeGroupId: 'g',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })
    wrapper.vm.isEditingGroups = true
    await nextTick()
    const del = wrapper.find('.bs-account-delete')
    expect(del.exists()).toBe(true)
    await del.trigger('click')
    await nextTick()
    const stored = JSON.parse(localStorage.getItem('accountGroups'))
    expect(stored.groups[0].accounts).toHaveLength(0)
  })

  it('disables add account row at five accounts', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          {
            id: 'g',
            name: 'G',
            accounts: [
              sampleAccounts[0],
              sampleAccounts[1],
              { id: 'a3', name: 'A3', adjusted_balance: 3 },
              { id: 'a4', name: 'A4', adjusted_balance: 4 },
              { id: 'a5', name: 'A5', adjusted_balance: 5 },
            ],
          },
        ],
        activeGroupId: 'g',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })
    await nextTick()
    expect(wrapper.find('.bs-add-account').classes()).toContain('bs-disabled')
  })

  it('marks the active group in the dropdown menu', async () => {
    localStorage.setItem(
      'accountGroups',
      JSON.stringify({
        groups: [
          { id: 'a', name: 'A', accounts: [] },
          { id: 'b', name: 'B', accounts: [] },
        ],
        activeGroupId: 'a',
      }),
    )
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    wrapper.vm.toggleGroupMenu()
    await nextTick()

    const activeItem = wrapper.find('.bs-group-item-active')
    expect(activeItem.exists()).toBe(true)
    expect(activeItem.text()).toContain('A')
    expect(activeItem.find('svg').exists()).toBe(true)
  })

  it('shifts tab window when active group moves out of view', async () => {
    const groups = Array.from({ length: 5 }, (_, i) => ({
      id: `g${i + 1}`,
      name: `G${i + 1}`,
      accounts: [],
    }))
    localStorage.setItem('accountGroups', JSON.stringify({ groups, activeGroupId: 'g1' }))
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    const tabTexts = () => wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(tabTexts()).toEqual(['G1', 'G2', 'G3'])

    wrapper.vm.setActiveGroup('g4')
    await nextTick()
    expect(wrapper.vm.visibleGroupIndex).toBe(1)
    expect(tabTexts()).toEqual(['G2', 'G3', 'G4'])

    wrapper.vm.setActiveGroup('g5')
    await nextTick()
    expect(wrapper.vm.visibleGroupIndex).toBe(2)
    expect(tabTexts()).toEqual(['G3', 'G4', 'G5'])
  })
})
