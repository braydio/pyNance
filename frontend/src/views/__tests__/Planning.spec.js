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

  const mountPlanning = () =>
    shallowMount(Planning, {
      global: {
        stubs: {
          BasePageLayout: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div><slot name="title" /><slot name="subtitle" /></div>' },
          UiButton: { template: '<button v-bind="$attrs"><slot /></button>' },
          Card: { template: '<div v-bind="$attrs"><slot /></div>' },
          BillList: { template: '<div class="bill-list-marker"><slot name="actions" /></div>' },
          BillForm: true,
          Allocator: true,
          PlanningSummary: true,
        },
      },
    })

  it('does not render internal design notes', () => {
    const text = mountPlanning().html()
    expect(text).not.toContain('handful of notes')
    expect(text).not.toContain('Gamefied')
    expect(text).not.toContain('<p1')
  })

  it('leads with the summary and shows BillForm only during an explicit task', async () => {
    const wrapper = mountPlanning()
    const html = wrapper.html()
    expect(html.indexOf('planning-summary-stub')).toBeLessThan(html.indexOf('bill-list-marker'))
    expect(wrapper.find('[data-testid="bill-form-panel"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-testid="add-bill"]')).toHaveLength(1)

    await wrapper.get('[data-testid="add-bill"]').trigger('click')
    expect(wrapper.find('[data-testid="bill-form-panel"]').exists()).toBe(true)
  })
})
