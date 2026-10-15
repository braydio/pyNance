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
  default: {
    props: ['selectedAspect', 'viewType'],
    template:
      '<div class="forecast-chart-stub" :data-selected-aspect="selectedAspect" :data-view-type="viewType" />',
  },
}))

vi.mock('../ForecastAdjustmentsForm.vue', () => ({
  default: { template: '<div class="forecast-adjustments-form-stub" />' },
}))

import ForecastLayout from '../ForecastLayout.vue'

function buildUseForecastDataReturn(
  adjustments: Array<Record<string, unknown>>,
  cashflows: Array<Record<string, unknown>> = [],
) {
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
    cashflows: computed(() => cashflows),
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
          adjustment_type: 'auto_income',
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

  it('keeps timeframe intact while sending the selected chart aspect to the chart', async () => {
    useForecastDataMock.mockReturnValue(buildUseForecastDataReturn([]))

    const wrapper = mount(ForecastLayout, {})
    await flushPromises()

    const chartStub = wrapper.get('.forecast-chart-stub')
    expect(chartStub.attributes('data-view-type')).toBe('Month')
    expect(chartStub.attributes('data-selected-aspect')).toBe('balances')

    const aspectSelect = wrapper.get('select')
    await aspectSelect.setValue('spending')

    expect(chartStub.attributes('data-view-type')).toBe('Month')
    expect(chartStub.attributes('data-selected-aspect')).toBe('spending')
  })

  it('opens and closes the cashflow details modal for selected breakdown items', async () => {
    useForecastDataMock.mockReturnValue(
      buildUseForecastDataReturn(
        [],
        [
          {
            date: '2026-03-25',
            label: 'Employer Payroll',
            amount: 1200,
            category: 'Income',
            source: 'recurring',
            confidence: 0.88,
            sources: [
              {
                type: 'recurring_rule',
                transaction_id: 'txn-100',
                date: '2026-03-12',
                description: 'Employer Payroll',
                category_display: 'Income - Wages',
                tags: ['payroll'],
              },
            ],
          },
        ],
      ),
    )

    const wrapper = mount(ForecastLayout, {})
    await flushPromises()

    expect(wrapper.find('.forecast-item-modal').exists()).toBe(false)
    await wrapper.get('.line-item-button').trigger('click')

    expect(wrapper.text()).toContain('Source transactions/events')
    expect(wrapper.text()).toContain('Employer Payroll')
    expect(wrapper.text()).toContain('Income - Wages')
    expect(wrapper.text()).toContain('Tags payroll')
    expect(wrapper.text()).toContain('Recurring rule')

    await wrapper.get('.forecast-item-modal__close').trigger('click')
    expect(wrapper.find('.forecast-item-modal').exists()).toBe(false)
  })

  it('shows an empty source state when selected cashflow item has no attached sources', async () => {
    useForecastDataMock.mockReturnValue(
      buildUseForecastDataReturn(
        [],
        [
          {
            date: '2026-03-25',
            label: 'Uncategorized delta',
            amount: -20,
            category: 'Uncategorized',
            source: 'uncategorized',
            confidence: 0.3,
          },
        ],
      ),
    )

    const wrapper = mount(ForecastLayout, {})
    await flushPromises()
    await wrapper.get('.line-item-button').trigger('click')

    expect(wrapper.text()).toContain(
      'No source transactions or events are attached to this forecast item.',
    )
  })

  it('puts the chart before assumptions and advanced controls, collapsed by default', async () => {
    useForecastDataMock.mockReturnValue(
      buildUseForecastDataReturn([
        {
          label: 'Auto wage income',
          amount: 1200,
          date: '2026-03-28',
          adjustment_type: 'auto_income',
          metadata: { source_transactions: [{ id: 'txn-1', amount: 1200 }] },
        },
      ]),
    )
    const wrapper = mount(ForecastLayout, {})
    await flushPromises()

    const html = wrapper.html()
    expect(html.indexOf('forecast-chart-stub')).toBeLessThan(
      html.indexOf('data-testid="assumptions"'),
    )
    expect(html.indexOf('data-testid="assumptions"')).toBeLessThan(
      html.indexOf('data-testid="advanced-controls"'),
    )

    const advanced = wrapper.get('[data-testid="advanced-controls"]')
    expect(advanced.attributes('open')).toBeUndefined()
    expect(advanced.text()).toContain('Graph mode')
    expect(advanced.text()).toContain('Moving average')
    expect(wrapper.get('[data-testid="basic-controls"]').text()).toContain('Chart aspect')

    const assumptions = wrapper.get('[data-testid="assumptions"]')
    expect(assumptions.attributes('open')).toBeUndefined()
    expect(assumptions.get('summary').text()).toContain('0 manual, 1 auto-detected')
    expect(assumptions.text()).toContain('View source transactions')
  })

  it('uses the theme instead of hardcoded light backgrounds and grays, with one gutter owner', async () => {
    useForecastDataMock.mockReturnValue(buildUseForecastDataReturn([]))
    const wrapper = mount(ForecastLayout)
    await flushPromises()
    const root = wrapper.get('.forecast-layout')
    expect(root.classes()).not.toContain('bg-gray-50')
    expect(root.classes()).not.toContain('p-6')
    expect(wrapper.html()).not.toMatch(/text-gray-|text-red-600|bg-gray-/)
  })

  it('renders status messages with roles and themed text classes', async () => {
    const loading = buildUseForecastDataReturn([])
    loading.loading = computed(() => true)
    useForecastDataMock.mockReturnValue(loading)
    const wrapper = mount(ForecastLayout)
    await flushPromises()
    const status = wrapper.get('[role="status"]')
    expect(status.text()).toContain('Loading forecast data')
    expect(status.classes()).toContain('text-muted')

    const failing = buildUseForecastDataReturn([])
    failing.error = computed(() => new Error('boom'))
    useForecastDataMock.mockReturnValue(failing)
    const errored = mount(ForecastLayout)
    await flushPromises()
    const alert = errored.get('[role="alert"]')
    expect(alert.text()).toContain('boom')
    expect(alert.classes()).toContain('text-negative')
  })

  it('orders results first, assumptions as a closed disclosure, advanced controls last', async () => {
    useForecastDataMock.mockReturnValue(buildUseForecastDataReturn([]))
    const wrapper = mount(ForecastLayout)
    await flushPromises()
    const html = wrapper.html()
    const order = [
      'summary-panel-stub',
      'basic-controls',
      'forecast-chart-stub',
      'data-testid="assumptions"',
      'data-testid="advanced-controls"',
    ].map((marker) => html.indexOf(marker))
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
    expect(wrapper.get('[data-testid="assumptions"]').attributes('open')).toBeUndefined()
    expect(wrapper.get('[data-testid="advanced-controls"]').attributes('open')).toBeUndefined()
  })

  it('aligns control fields with a shared label/select pattern and nests at most one card level in assumptions', async () => {
    useForecastDataMock.mockReturnValue(buildUseForecastDataReturn([]))
    const wrapper = mount(ForecastLayout)
    await flushPromises()
    const fields = wrapper.findAll('.control-field')
    expect(fields.length).toBeGreaterThanOrEqual(2)
    fields.forEach((field) => {
      expect(field.find('.control-field__label').exists()).toBe(true)
      expect(field.find('select').classes()).toContain('select')
    })
    expect(wrapper.find('[data-testid="assumptions"] .card .card').exists()).toBe(false)
    expect(wrapper.find('[data-testid="assumptions"] .adjustments-grid.card').exists()).toBe(false)
  })
})
