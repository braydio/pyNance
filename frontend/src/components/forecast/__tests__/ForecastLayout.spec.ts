// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { computed, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const useForecastDataMock = vi.fn()
const getAccountsMock = vi.fn()

vi.mock('@/composables/useForecastData', () => ({
  useForecastData: (...args: unknown[]) => useForecastDataMock(...args),
}))

vi.mock('@/composables/useAccountGroups', () => ({
  useAccountGroups: () => ({
    groups: ref([]),
  }),
}))

vi.mock('@/services/api', () => ({
  default: {
    getAccounts: (...args: unknown[]) => getAccountsMock(...args),
  },
}))

vi.mock('../ForecastSummaryPanel.vue', () => ({
  default: { template: '<div class="summary-panel-stub" />' },
}))

vi.mock('../ForecastChart.vue', () => ({
  default: { template: '<div class="forecast-chart-stub" />' },
}))

vi.mock('../ForecastBreakdown.vue', () => ({
  default: { template: '<div class="forecast-breakdown-stub" />' },
}))

vi.mock('../ForecastAdjustmentsForm.vue', () => ({
  default: { template: '<div class="forecast-adjustments-form-stub" />' },
}))

import ForecastLayout from '../ForecastLayout.vue'

function buildUseForecastDataReturn(adjustments: Array<Record<string, unknown>>) {
  return {
    timeline: computed(() => [
      { date: '2026-03-23', label: '2026-03-23', forecast_balance: 100, actual_balance: null },
    ]),
    summary: computed(() => ({
      average_daily_change: 0,
      metadata: {},
      net_change: 25,
      starting_balance: 100,
    })),
    adjustments: computed(() => adjustments),
    cashflows: computed(() => []),
    series: computed(() => ({
      manual_adjustments: { id: 'manual_adjustments', label: 'Manual adjustments', points: [] },
      realized_income: { id: 'realized_income', label: 'Realized income', points: [] },
    })),
    metadata: computed(() => ({ lookback_days: 90 })),
    loading: computed(() => false),
    error: computed(() => null),
    fetchData: vi.fn().mockResolvedValue(undefined),
  }
}

describe('ForecastLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getAccountsMock.mockResolvedValue({
      accounts: [{ account_id: 'acc-1', name: 'Checking', institution_name: 'Bank' }],
    })
  })

  it('shows source transaction drill-down content for auto-detected adjustments with references', async () => {
    useForecastDataMock.mockReturnValue(
      buildUseForecastDataReturn([
        {
          label: 'Auto wage income',
          amount: 1200,
          date: '2026-03-28',
          adjustment_type: 'auto_income',
          reason: 'Derived from recent wage-category transactions.',
          metadata: {
            source_transactions: [
              {
                id: 'txn-1',
                date: '2026-03-14',
                amount: 1200,
                description: 'Employer Payroll',
                matching_fields: {
                  category_display: 'Income - Wages',
                  category_slug: 'income-wages',
                  tags: ['payroll'],
                },
              },
            ],
          },
        },
      ]),
    )

    const wrapper = mount(ForecastLayout, {})

    await flushPromises()

    expect(wrapper.text()).toContain('Auto-Detected Adjustments')
    expect(wrapper.text()).toContain('Auto wage income')
    expect(wrapper.text()).toContain('View source transactions')

    await wrapper.get('button.auto-adjustment-toggle').trigger('click')

    expect(wrapper.text()).toContain('Employer Payroll')
    expect(wrapper.text()).toContain('2026-03-14')
    expect(wrapper.text()).toContain('txn-1')
    expect(wrapper.text()).toContain('Matching fields: display Income - Wages')
    expect(wrapper.text()).toContain('slug income-wages')
    expect(wrapper.text()).toContain('tags payroll')
  })

  it('hides the drill-down toggle and shows a graceful empty state when sources are absent', async () => {
    useForecastDataMock.mockReturnValue(
      buildUseForecastDataReturn([
        {
          label: 'Historical 30d avg/day',
          amount: 15,
          date: 'daily trend',
          adjustment_type: 'auto_trend',
          reason: 'Derived from historical average net change.',
          metadata: {},
        },
      ]),
    )

    const wrapper = mount(ForecastLayout, {})

    await flushPromises()

    expect(wrapper.text()).toContain('Historical 30d avg/day')
    expect(wrapper.find('button.auto-adjustment-toggle').exists()).toBe(false)
    expect(wrapper.text()).toContain(
      'No source transactions are available for this auto-detected adjustment.',
    )
  })
})
