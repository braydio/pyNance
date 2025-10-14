// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Planning from '../Planning.vue'

const mockState = {
  version: 4,
  devMode: false,
  mode: 'local',
  bills: [
    {
      id: 'b1',
      name: 'Rent',
      amountCents: 120000,
      dueDate: '2024-07-01',
      frequency: 'monthly',
      category: 'Housing',
      origin: 'manual',
      accountId: 'acct-1',
      scenarioId: 's1',
    },
  ],
  scenarios: [
    {
      id: 's1',
      name: 'Baseline',
      planningBalanceCents: 500000,
      allocations: [],
      accountId: 'acct-1',
      currencyCode: 'USD',
    },
  ],
  activeScenarioId: 's1',
  activeScenarioIdByAccount: { 'acct-1': 's1' },
  lastSavedAt: new Date().toISOString(),
}

const planningMocks = vi.hoisted(() => ({
  ensureScenarioForAccount: vi.fn(() => mockState.scenarios[0]),
  persistBill: vi.fn(),
  removeBill: vi.fn(),
  persistScenarioAllocations: vi.fn(),
}))

vi.mock('@/composables/usePlanning', () => ({
  usePlanning: () => ({ state: mockState }),
  ...planningMocks,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { accountId: 'acct-1' } }),
}))

describe('Planning.vue', () => {
  it('renders planning components with scenario context', () => {
    const wrapper = shallowMount(Planning, {
      global: {
        stubs: {
          BasePageLayout: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div><slot /></div>' },
          UiButton: true,
          Card: { template: '<div><slot /></div>' },
          BillList: true,
          BillForm: true,
          Allocator: true,
          PlanningSummary: true,
        },
      },
    })

    const summaryStub = wrapper.findComponent({ name: 'PlanningSummary' })
    expect(summaryStub.exists()).toBe(true)
    expect(summaryStub.props('scenarioId')).toBe('s1')
    expect(planningMocks.ensureScenarioForAccount).toHaveBeenCalledWith('acct-1')
  })
})
