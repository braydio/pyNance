// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import PlanningSummary from '../PlanningSummary.vue'

const mockState = {
  version: 4,
  devMode: false,
  mode: 'local',
  bills: [],
  scenarios: [
    {
      id: 'scenario-1',
      name: 'Plan for acct-123',
      planningBalanceCents: 250000,
      allocations: [],
      accountId: 'acct-123',
      currencyCode: 'USD',
    },
  ],
  activeScenarioId: 'scenario-1',
  activeScenarioIdByAccount: { 'acct-123': 'scenario-1' },
  lastSavedAt: new Date().toISOString(),
}

vi.mock('@/composables/usePlanning', () => ({
  usePlanning: () => ({ state: mockState }),
}))

vi.mock('@/selectors/planning', () => ({
  selectActiveScenario: () => mockState.scenarios[0],
  selectAllocatedCents: () => 0,
  selectRemainingCents: () => 0,
  selectTotalBillsCents: () => 0,
}))

const apiMocks = vi.hoisted(() => ({
  getAccounts: vi.fn(async () => ({
    status: 'success',
    accounts: [
      {
        account_id: 'acct-123',
        name: 'Primary Checking',
        institution_name: 'PyBank',
      },
    ],
  })),
}))

vi.mock('@/services/api', () => ({
  default: apiMocks,
}))

vi.mock('@/components/ui/Button.vue', () => ({
  default: {
    name: 'UiButton',
    template: '<button><slot /></button>',
  },
}))

describe('PlanningSummary', () => {
  it('shows a friendly planning account label instead of the account ID', async () => {
    const wrapper = mount(PlanningSummary, {
      props: { scenarioId: 'scenario-1' },
    })

    await flushPromises()

    const heading = wrapper.get('h3')
    expect(heading.text()).toContain('Plan for Primary Checking · PyBank')
    expect(wrapper.text()).toContain('Planning account Primary Checking · PyBank')
  })
})
