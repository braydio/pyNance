// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, watch, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

// Sample accounts include six assets and one liability
const assetAccounts = Array.from({ length: 6 }, (_, i) => ({
  id: `asset-${i + 1}`,
  name: `Asset ${i + 1}`,
  adjusted_balance: i + 1,
}))
const liabilityAccount = { id: 'debt-1', name: 'Debt 1', adjusted_balance: -1 }

// --- Composable Mocks ---

// Mock useTopAccounts to return the sample accounts while enforcing the
// five‑account visibility limit used by the real composable.
vi.mock('@/composables/useTopAccounts', () => {
  const accounts = ref([])
  const allVisibleAccounts = ref([])
  const fetchAccounts = vi.fn(() => {
    accounts.value = [...assetAccounts, liabilityAccount]
    // only expose five asset accounts plus any liabilities
    allVisibleAccounts.value = [...assetAccounts.slice(0, 5), liabilityAccount]
  })
  return {
    useTopAccounts: () => ({ accounts, allVisibleAccounts, fetchAccounts }),
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

      return { groups, activeGroupId }
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

    // trigger account fetch and watchers
    await nextTick()

    // default group exists
    const names = wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(names).toContain('Group')

    // add and rename a group
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

  it('limits visible accounts to five per group', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    const assets = wrapper.vm.groups.find((g) => g.id === 'assets')
    expect(assets.accounts.length).toBe(5)
    const accountNames = assets.accounts.map((a) => a.name)
    expect(accountNames).not.toContain('Asset 6')
  })

  it('updates group order when accounts are reordered', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: { stubs: { AccountSparkline: true } },
    })

    await nextTick()
    await nextTick()
    const assetsIdx = wrapper.vm.groups.findIndex((g) => g.id === 'assets')
    wrapper.vm.activeGroupId = 'assets'
    await nextTick()
    const firstBefore = wrapper.findAll('.bs-name')[0].text()
    wrapper.vm.groups[assetsIdx].accounts.reverse()
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
})
