// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import { nextTick } from 'vue'
import FinancialSummary from '../FinancialSummary.vue'

vi.mock('@/services/api', () => ({
  default: {
    getAccountSnapshot: vi.fn(async () => ({
      data: { selected_account_ids: ['acc-1'] },
    })),
  },
}))

vi.mock('@/api/recurring', () => ({
  getRecurringTransactions: vi.fn(async () => ({
    status: 'success',
    reminders: [],
  })),
}))

const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

describe('FinancialSummary trends', () => {
  it('uses shared accent utility classes for the global detail toggle', () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 300, totalExpenses: 200, totalNet: 100 },
        chartData: [],
      },
      global: {
        stubs: {
          DailySpendingPanel: {
            template: '<div data-test="daily-spending-panel"></div>',
          },
        },
      },
    })

    const globalToggle = wrapper.get('.stats-controls .accent-toggle-btn')
    expect(globalToggle.classes()).toContain('accent-toggle-btn')
  })
  it('shows the daily spending panel only in extended view', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 300, totalExpenses: 200, totalNet: 100 },
        chartData: [],
      },
      global: {
        stubs: {
          DailySpendingPanel: {
            template: '<div data-test="daily-spending-panel"></div>',
          },
        },
      },
    })

    expect(wrapper.find('[data-test="daily-spending-panel"]').exists()).toBe(false)

    await wrapper.find('.accent-toggle-btn').trigger('click')
    await nextTick()

    expect(wrapper.find('[data-test="daily-spending-panel"]').exists()).toBe(true)
  })
  it('shows income and expense trend deltas', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 300, totalExpenses: 200, totalNet: 100 },
        chartData: [
          {
            date: '2024-01-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 50 },
          },
          {
            date: '2024-01-02',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -150 },
            net: { parsedValue: 50 },
          },
        ],
      },
    })

    await wrapper.find('.accent-toggle-btn').trigger('click')
    const html = wrapper.html()
    expect(html).toContain('Income:')
    expect(html).toContain('$100.00')
    expect(html).toContain('Expenses:')
    expect(html).toContain('$100.00')
  })

  it('uses accounting formatting and polarity classes for trend and outlier amounts', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
        chartData: [
          {
            date: '2024-02-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: 0 },
            net: { parsedValue: 100 },
          },
          {
            date: '2024-02-02',
            income: { parsedValue: 50 },
            expenses: { parsedValue: -100 },
            net: { parsedValue: -50 },
          },
        ],
      },
    })

    await wrapper.find('.accent-toggle-btn').trigger('click')
    await nextTick()

    const trendValues = wrapper.findAll('.trend-indicator')
    expect(trendValues[0].text()).toBe('($150.00)')
    expect(trendValues[0].classes()).toContain('amount-negative')
    expect(trendValues[1].text()).toBe('($50.00)')
    expect(trendValues[1].classes()).toContain('amount-negative')
    expect(trendValues[2].text()).toBe('$100.00')
    expect(trendValues[2].classes()).toContain('amount-positive')

    const outlierAmounts = wrapper.findAll('.outlier-amount')
    expect(outlierAmounts[0].text()).toBe('$100.00')
    expect(outlierAmounts[0].classes()).toContain('amount-positive')
    expect(outlierAmounts[1].text()).toBe('($100.00)')
    expect(outlierAmounts[1].classes()).toContain('amount-negative')
  })

  it('rolls summary totals back to the selected date', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 600, totalExpenses: 300, totalNet: 300 },
        chartData: [
          {
            date: '2024-01-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 50 },
          },
          {
            date: '2024-01-02',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -100 },
            net: { parsedValue: 100 },
          },
          {
            date: '2024-01-03',
            income: { parsedValue: 300 },
            expenses: { parsedValue: -150 },
            net: { parsedValue: 150 },
          },
        ],
      },
    })

    await wrapper.find('.accent-toggle-btn').trigger('click')
    const dateInput = wrapper.find('input[type="date"]')
    await dateInput.setValue('2024-01-02')
    await nextTick()

    const incomeStat = wrapper.find('.stat-income .stat-value').text()
    const expenseStat = wrapper.find('.stat-expenses .stat-value').text()
    const netStat = wrapper.find('.stat-net .stat-value').text()

    expect(incomeStat).toContain('$300.00')
    expect(expenseStat).toContain('($150.00)')
    expect(netStat).toContain('$150.00')
    expect(wrapper.find('.stat-income .stat-value').classes()).toContain('amount-positive')
    expect(wrapper.find('.stat-expenses .stat-value').classes()).toContain('amount-negative')
    expect(wrapper.find('.stat-net .stat-value').classes()).toContain('amount-positive')

    expect(wrapper.find('.detail-date-helper').text()).toMatch(/2024/)
  })

  it('only renders the reset button when using a custom detail date', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 600, totalExpenses: 300, totalNet: 300 },
        chartData: [
          {
            date: '2024-01-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 50 },
          },
          {
            date: '2024-01-02',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -100 },
            net: { parsedValue: 100 },
          },
        ],
      },
    })

    await wrapper.find('.accent-toggle-btn').trigger('click')
    expect(wrapper.find('.detail-date-reset').exists()).toBe(false)

    const dateInput = wrapper.get('#financial-snapshot-detail-date')
    await dateInput.setValue('2024-01-01')
    await nextTick()

    expect(wrapper.find('.detail-date-reset').exists()).toBe(true)

    await wrapper.find('.detail-date-reset').trigger('click')
    await nextTick()

    expect(wrapper.find('.detail-date-reset').exists()).toBe(false)
  })

  it('includes zero-value days when calculating averages and moving averages', async () => {
    const wrapper = mount(FinancialSummary, {
      props: {
        summary: { totalIncome: 150, totalExpenses: 70, totalNet: 80 },
        startDate: '2024-04-01',
        endDate: '2024-04-05',
        chartData: [
          {
            date: '2024-04-01',
            income: { parsedValue: 100 },
            expenses: { parsedValue: -20 },
            net: { parsedValue: 80 },
          },
          {
            date: '2024-04-03',
            income: { parsedValue: 50 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 0 },
          },
        ],
      },
    })

    await wrapper.find('.accent-toggle-btn').trigger('click')
    await nextTick()

    const metrics = wrapper.vm.extendedMetrics

    expect(metrics.avgDailyIncome).toBeCloseTo(30)
    expect(metrics.avgDailyExpenses).toBeCloseTo(-14)
    expect(metrics.avgDailyNet).toBeCloseTo(16)
    // Only 5 days of history: trailing windows are not available yet.
    expect(metrics.netMA7).toBeNull()
    expect(metrics.netMA30).toBeNull()
    expect(wrapper.find('.stat-ma7').text()).toContain('N/A (needs 7 days)')
    expect(wrapper.find('.stat-ma30').text()).toContain('N/A (needs 30 days)')
  })
})

const stubs = {
  DailySpendingPanel: { template: '<div data-test="daily-spending-panel"></div>' },
  RouterLink: RouterLinkStub,
}

async function settle() {
  await nextTick()
  await flushPromises()
  await nextTick()
  await flushPromises()
}

function mountSummary(props = {}) {
  return mount(FinancialSummary, {
    props: {
      summary: { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
      chartData: [],
      ...props,
    },
    global: { stubs },
  })
}

function day(date, income, expense) {
  return {
    date,
    income: { parsedValue: income },
    expenses: { parsedValue: expense },
    net: { parsedValue: income + expense },
  }
}

describe('FinancialSummary detail hierarchy', () => {
  it('collapsed state is a quiet row with accessible toggle and no totals', async () => {
    const wrapper = mountSummary({
      summary: { totalIncome: 300, totalExpenses: -200, totalNet: 100 },
      startDate: '2024-01-01',
      endDate: '2024-01-31',
    })
    const toggle = wrapper.get('.accent-toggle-btn')
    expect(toggle.attributes('type')).toBe('button')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    expect(toggle.attributes('aria-controls')).toBe('financial-details-panel')
    expect(toggle.text()).toBe('Show details')
    expect(wrapper.text()).toContain('Financial details')
    expect(wrapper.text()).toContain('Selected period')
    expect(wrapper.text()).not.toContain('Net cash flow')
    expect(wrapper.find('.stat-income').exists()).toBe(false)

    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('#financial-details-panel').exists()).toBe(true)
  })

  it('orders expanded content: date, upcoming, spending, period, more statistics', async () => {
    const wrapper = mountSummary({ chartData: [day('2024-01-01', 100, -50)] })
    await wrapper.get('.accent-toggle-btn').trigger('click')
    await settle()
    const html = wrapper.html()
    const order = [
      'detail-date-controls',
      'recurring-upcoming-panel',
      'data-test="daily-spending-panel"',
      'period-summary',
      'more-statistics',
    ].map((marker) => html.indexOf(marker))
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
    expect(wrapper.get('details.more-statistics').attributes('open')).toBeUndefined()
    expect(wrapper.text()).toContain('Net cash flow')
    expect(wrapper.text()).not.toMatch(/Savings|Increasing|Decreasing|Volatility|Low\b|Medium\b/)
    expect(wrapper.text()).toContain('First vs last day (not a period trend)')
    expect(wrapper.text()).toContain('Daily net standard deviation')
  })

  it('shows net as % of income only when income is positive', async () => {
    const withIncome = mountSummary({ chartData: [day('2024-01-01', 200, -50)] })
    await withIncome.get('.accent-toggle-btn').trigger('click')
    expect(withIncome.get('.stat-net-percent').text()).toContain('75%')

    const noIncome = mountSummary({ chartData: [day('2024-01-01', 0, -50)] })
    await noIncome.get('.accent-toggle-btn').trigger('click')
    expect(noIncome.find('.stat-net-percent').exists()).toBe(false)
  })

  it('computes 7 and 30 day averages only with full windows and keeps expense sign', async () => {
    const data = Array.from({ length: 8 }, (_, i) => day(`2024-03-0${i + 1}`, 100, -40))
    const wrapper = mountSummary({
      chartData: data,
      startDate: '2024-03-01',
      endDate: '2024-03-08',
    })
    await wrapper.get('.accent-toggle-btn').trigger('click')
    const m = wrapper.vm.extendedMetrics
    expect(m.netMA7).toBeCloseTo(60)
    expect(m.netMA30).toBeNull()
    expect(m.avgDailyExpenses).toBeCloseTo(-40)
  })

  it('reports not enough history for unusual days on short samples', async () => {
    const wrapper = mountSummary({
      chartData: [day('2024-01-01', 100, 0), day('2024-01-02', 0, -500)],
    })
    await wrapper.get('.accent-toggle-btn').trigger('click')
    expect(wrapper.get('.stat-unusual').text()).toContain('Not enough history')
    expect(wrapper.find('.unusual-day-btn').exists()).toBe(false)
  })

  it('lists up to three real unusual dates and emits select-date', async () => {
    const data = Array.from({ length: 20 }, (_, i) =>
      day(`2024-01-${String(i + 1).padStart(2, '0')}`, 0, 0),
    )
    data[3] = day('2024-01-04', 0, -900)
    data[9] = day('2024-01-10', 0, -800)
    const wrapper = mountSummary({
      chartData: data,
      startDate: '2024-01-01',
      endDate: '2024-01-20',
    })
    await wrapper.get('.accent-toggle-btn').trigger('click')
    const buttons = wrapper.findAll('.unusual-day-btn')
    expect(buttons.map((b) => b.text())).toEqual(['2024-01-04', '2024-01-10'])
    await buttons[0].trigger('click')
    expect(wrapper.emitted('select-date')[0]).toEqual(['2024-01-04'])
  })

  it('counts zero-activity days and positive/negative days over the padded range', async () => {
    const wrapper = mountSummary({
      chartData: [day('2024-04-01', 100, -20), day('2024-04-04', 0, -30)],
      startDate: '2024-04-01',
      endDate: '2024-04-04',
    })
    await wrapper.get('.accent-toggle-btn').trigger('click')
    expect(wrapper.text()).toContain('Based on 4 days')
    expect(wrapper.text()).toContain('25% (1/4)') // positive-net days
    expect(wrapper.text()).toContain('Average positive-net day')
  })
})

describe('FinancialSummary upcoming recurring', () => {
  beforeEach(async () => {
    const api = (await import('@/services/api')).default
    api.getAccountSnapshot.mockReset()
    api.getAccountSnapshot.mockResolvedValue({ data: { selected_account_ids: ['acc-1'] } })
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockReset()
    getRecurringTransactions.mockResolvedValue({ status: 'success', reminders: [] })
  })

  async function open(wrapper) {
    await wrapper.get('.accent-toggle-btn').trigger('click')
    await settle()
  }

  const auto = (description, due, occurrences, confidence, extra = {}) => ({
    source: 'auto',
    description,
    amount: '($10.00)',
    next_due_date: due,
    days_until_due: 3,
    auto_detection: { occurrences, confidence_score: confidence },
    ...extra,
  })

  it('sorts by due date before confidence and user items first on the same day', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockResolvedValue({
      status: 'success',
      reminders: [
        auto('Late High Confidence', '2026-04-12', 9, 99),
        auto('Auto Same Day', '2026-04-10', 9, 99),
        {
          source: 'user',
          description: 'User Same Day',
          amount: '($5.00)',
          next_due_date: '2026-04-10',
          days_until_due: 3,
        },
        auto('Early Low Confidence', '2026-04-09', 1, 10),
      ],
    })
    const wrapper = mountSummary()
    await open(wrapper)
    expect(wrapper.findAll('.recurring-upcoming-description').map((n) => n.text())).toEqual([
      'Early Low Confidence',
      'User Same Day',
      'Auto Same Day',
      'Late High Confidence',
    ])
  })

  it('labels scheduled vs likely recurring and shows API amount as-is', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockResolvedValue({
      status: 'success',
      reminders: [
        auto('Streaming', '2026-04-10', 6, 92, { days_until_due: 0 }),
        {
          source: 'user',
          description: 'Rent',
          amount: '($1,200.00)',
          next_due_date: '2026-04-11',
          days_until_due: 1,
        },
      ],
    })
    const wrapper = mountSummary()
    await open(wrapper)
    const items = wrapper.findAll('.recurring-upcoming-item')
    expect(items[0].text()).toContain('Today')
    expect(items[0].text()).toContain('Likely recurring')
    expect(items[0].text()).toContain('based on 6 matches')
    expect(items[0].text()).toContain('($10.00)')
    expect(items[1].text()).toContain('Tomorrow')
    expect(items[1].text()).toContain('Scheduled')
    expect(items[1].text()).not.toContain('based on')
    expect(items[1].text()).toContain('($1,200.00)')
    expect(wrapper.text()).toContain('Due in the next 7 days')
    expect(wrapper.text()).toContain('As of today')
  })

  it('limits to six rows and counts the rest', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockResolvedValue({
      status: 'success',
      reminders: Array.from({ length: 8 }, (_, i) => auto(`Item ${i}`, '2026-04-10', 3, 50)),
    })
    const wrapper = mountSummary()
    await open(wrapper)
    expect(wrapper.findAll('.recurring-upcoming-item')).toHaveLength(6)
    expect(wrapper.get('.recurring-upcoming-more').text()).toContain('+2 more due in 7 days')
  })

  it('distinguishes no selected accounts from nothing due', async () => {
    const api = (await import('@/services/api')).default
    api.getAccountSnapshot.mockResolvedValue({ data: { selected_account_ids: [] } })
    const none = mountSummary()
    await open(none)
    expect(none.text()).toContain('No accounts are selected')

    api.getAccountSnapshot.mockResolvedValue({ data: { selected_account_ids: ['a'] } })
    const empty = mountSummary()
    await open(empty)
    expect(empty.text()).toContain('No recurring items due in the next 7 days')
    expect(empty.text()).not.toContain('No accounts are selected')
  })

  it('shows an error with retry when every account fails, then recovers', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockRejectedValue(new Error('down'))
    const wrapper = mountSummary()
    await open(wrapper)
    expect(wrapper.text()).toContain('Unable to load upcoming recurring transactions')

    getRecurringTransactions.mockResolvedValue({
      status: 'success',
      reminders: [auto('Streaming', '2026-04-10', 6, 92)],
    })
    await wrapper.get('.recurring-upcoming-retry').trigger('click')
    await settle()
    expect(wrapper.text()).toContain('Streaming')
    expect(wrapper.text()).not.toContain('Unable to load')
  })

  it('keeps reminders from healthy accounts when another account fails', async () => {
    const api = (await import('@/services/api')).default
    api.getAccountSnapshot.mockResolvedValue({ data: { selected_account_ids: ['ok', 'bad'] } })
    const { getRecurringTransactions } = await import('@/api/recurring')
    getRecurringTransactions.mockImplementation(async (id) => {
      if (id === 'bad') throw new Error('nope')
      return { status: 'success', reminders: [auto('Streaming', '2026-04-10', 6, 92)] }
    })
    const wrapper = mountSummary()
    await open(wrapper)
    expect(wrapper.text()).toContain('Streaming')
    expect(wrapper.text()).toContain("Couldn't check 1 of 2 accounts")
  })

  it('refreshes stale reminders when details are reopened', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    const nowSpy = vi.spyOn(Date, 'now')
    nowSpy.mockReturnValue(1_000_000)
    const wrapper = mountSummary()
    await open(wrapper)
    expect(getRecurringTransactions).toHaveBeenCalledTimes(1)

    // Reopen within TTL: no refetch.
    await wrapper.get('.accent-toggle-btn').trigger('click')
    nowSpy.mockReturnValue(1_000_000 + 60_000)
    await open(wrapper)
    expect(getRecurringTransactions).toHaveBeenCalledTimes(1)

    // Reopen after the 5 minute TTL: refetch.
    await wrapper.get('.accent-toggle-btn').trigger('click')
    nowSpy.mockReturnValue(1_000_000 + 6 * 60_000)
    await open(wrapper)
    expect(getRecurringTransactions).toHaveBeenCalledTimes(2)
    nowSpy.mockRestore()
  })

  it('does not change the next-seven-day request when the historical date changes', async () => {
    const { getRecurringTransactions } = await import('@/api/recurring')
    const wrapper = mountSummary({
      chartData: [day('2024-01-01', 1, 0), day('2024-01-02', 1, 0)],
    })
    await open(wrapper)
    await wrapper.get('#financial-snapshot-detail-date').setValue('2024-01-01')
    await settle()
    expect(getRecurringTransactions).toHaveBeenCalledTimes(1)
    expect(wrapper.text()).toContain('As of today')
  })

  it('links to transactions without per-reminder actions', async () => {
    const wrapper = mountSummary()
    await open(wrapper)
    expect(wrapper.getComponent(RouterLinkStub).props('to')).toBe('/transactions')
    expect(wrapper.text()).not.toMatch(/Mark paid|\bPay\b/)
  })
})
