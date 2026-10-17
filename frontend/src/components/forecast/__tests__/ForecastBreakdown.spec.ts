import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ForecastBreakdown from '../ForecastBreakdown.vue'

const item = (over: Record<string, unknown> = {}) => ({
  date: '2026-11-03',
  amount: -10,
  label: 'Thing',
  category: 'scheduled_bill',
  source: 'recurring',
  metadata: { event_id: `ev-${Math.random()}` },
  ...over,
})

const paycheck = item({
  date: '2026-11-01',
  amount: 1200,
  label: 'ACME PAYROLL',
  category: 'scheduled_income',
  metadata: { event_id: 'pay' },
})
const electric = item({
  date: '2026-11-10',
  amount: -90,
  label: 'Duke Energy',
  category: 'scheduled_bill',
  metadata: { event_id: 'elec' },
})
const variable = item({
  date: '2026-11-04',
  amount: -45.23,
  label: 'residual',
  category: 'residual',
  metadata: { event_id: 'res1' },
})

const mountBreakdown = (items: unknown[], props: Record<string, unknown> = {}) =>
  mount(ForecastBreakdown, {
    props: { forecastItems: items, viewType: 'Month', ...props } as never,
  })

describe('ForecastBreakdown groups', () => {
  it('groups income, bills and variable spending whose totals add up to the net change', () => {
    const wrapper = mountBreakdown([paycheck, electric, variable])
    const text = (key: string) => wrapper.get(`[data-testid="group-${key}"]`).text()
    expect(text('income')).toContain('Expected income')
    expect(text('income')).toContain('+$1,200.00')
    expect(text('bills')).toContain('Scheduled bills & payments')
    expect(text('bills')).toContain('−$90.00')
    expect(text('variable')).toContain('Estimated variable spending')
    expect(text('variable')).toContain('−$45.23')
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('+$1,064.77') // 1200 - 90 - 45.23
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('3 cash events')
  })

  it('uses real currency formatting for every amount (no raw floats or missing separators)', () => {
    const wrapper = mountBreakdown([
      item({ amount: -1234.5, category: 'scheduled_bill', metadata: { event_id: 'big' } }),
    ])
    expect(wrapper.text()).toContain('−$1,234.50')
    expect(wrapper.text()).not.toMatch(/\$\d+\.\d{1}(?!\d)/)
    expect(wrapper.text()).not.toMatch(/-\$\d/) // true minus sign, not a hyphen-minus
  })

  it('does not show outstanding debt as a cash event, and puts a debt payment under bills as an outflow', () => {
    const payment = item({
      amount: -500,
      label: 'Card payment',
      category: 'liability_payment',
      metadata: { event_id: 'pay1' },
    })
    const wrapper = mountBreakdown([payment, paycheck])
    expect(wrapper.text()).not.toContain('11,686.65')
    expect(wrapper.get('[data-testid="group-bills"]').text()).toContain('−$500.00')
    expect(wrapper.get('[data-testid="group-bills"]').text()).toContain(
      'Scheduled bills & payments',
    )
  })

  it('counts every event at most once, even if it appears twice', () => {
    const wrapper = mountBreakdown([electric, { ...electric }, paycheck])
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('2 cash events')
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('+$1,110.00')
  })

  it('sums in whole cents so floating point never leaks into totals', () => {
    const items = [0.1, 0.2, 0.3].map((amount, i) =>
      item({
        amount: -amount,
        category: 'residual',
        metadata: { event_id: `r${i}` },
        date: `2026-11-0${i + 1}`,
      }),
    )
    const wrapper = mountBreakdown(items)
    expect(wrapper.get('[data-testid="group-variable"] summary').text()).toContain('−$0.60')
  })

  it('skips rows with no usable amount instead of inventing zero', () => {
    const wrapper = mountBreakdown([item({ amount: null }), item({ amount: 'n/a' }), paycheck])
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('1 cash event')
  })

  it('collapses 100 daily residual rows: weekday labels, 15 shown, then everything on request', async () => {
    const days = Array.from({ length: 100 }, (_, i) => {
      const date = new Date(Date.UTC(2026, 10, 1 + i)).toISOString().slice(0, 10)
      return item({
        date,
        amount: -12.5,
        label: 'residual',
        category: 'residual',
        metadata: { event_id: `r${i}` },
      })
    })
    const wrapper = mountBreakdown(days)
    const group = wrapper.get('[data-testid="group-variable"]')
    expect(group.get('summary').text()).toContain('100 items')
    expect(group.get('summary').text()).toContain('−$1,250.00')
    expect(group.findAll('.line-item-button')).toHaveLength(15)
    expect(group.text()).toContain('Typical spending')
    expect(group.text()).toMatch(/Sun 2026-11-01/)
    await group.get('[data-testid="show-all-variable"]').trigger('click')
    expect(group.findAll('.line-item-button')).toHaveLength(100)
    expect(group.find('[data-testid="show-all-variable"]').exists()).toBe(false)
  })

  it('keeps the drill-in event and passes the original item', async () => {
    const wrapper = mountBreakdown([electric])
    await wrapper.get('[data-testid="row-e-elec"]').trigger('click')
    expect(wrapper.emitted('select-item')![0][0]).toEqual(electric)
  })

  it('groups V1 rows by sign and adjustments by name', () => {
    const wrapper = mountBreakdown([
      item({ amount: 300, category: 'Salary', label: 'Salary', metadata: undefined }),
      item({ amount: -60, category: 'Subscription', label: 'Netflix', metadata: undefined }),
      item({ amount: -25, category: 'Adjustment', label: 'Manual', metadata: undefined }),
    ])
    expect(wrapper.find('[data-testid="group-other_in"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="group-other_out"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="group-adjustments"]').text()).toContain('−$25.00')
  })

  it('shows an empty state and groups nothing', () => {
    const wrapper = mountBreakdown([])
    expect(wrapper.text()).toContain('No forecast cashflows available.')
    expect(wrapper.find('[data-testid="breakdown-net"]').exists()).toBe(false)
  })

  it('formats driver amounts with the shared helper and keeps them out of the cash totals', () => {
    const wrapper = mountBreakdown([paycheck], {
      modelVersion: 'v2',
      drivers: [
        {
          event_id: 'pay',
          source_id: 's',
          date: '2026-11-01',
          amount: 1200,
          kind: 'scheduled_income',
          origin: 'manual_rule',
          confidence_label: 'high',
          label: 'ACME PAYROLL',
        },
      ],
    })
    expect(wrapper.get('.driver-amount').text()).toBe('+$1,200.00')
    expect(wrapper.get('[data-testid="breakdown-net"]').text()).toContain('+$1,200.00') // not doubled
  })
})
