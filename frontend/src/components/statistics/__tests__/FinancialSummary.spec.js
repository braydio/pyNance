// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import FinancialSummary from '../FinancialSummary.vue'

describe('FinancialSummary trends', () => {
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

    await wrapper.find('.gradient-toggle-btn').trigger('click')
    const html = wrapper.html()
    expect(html).toContain('Income:')
    expect(html).toContain('+\$100.00')
    expect(html).toContain('Expenses:')
    expect(html).toContain('+\$100.00')
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

    await wrapper.find('.gradient-toggle-btn').trigger('click')
    const dateInput = wrapper.find('input[type="date"]')
    await dateInput.setValue('2024-01-02')
    await nextTick()

    const incomeStat = wrapper.find('.stat-income .stat-value').text()
    const expenseStat = wrapper.find('.stat-expenses .stat-value').text()
    const netStat = wrapper.find('.stat-net .stat-value').text()

    expect(incomeStat).toContain('$300.00')
    expect(expenseStat).toContain('($150.00)')
    expect(netStat).toContain('$150.00')

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

    await wrapper.find('.gradient-toggle-btn').trigger('click')
    expect(wrapper.find('.detail-date-reset').exists()).toBe(false)

    const dateInput = wrapper.get('#financial-snapshot-detail-date')
    await dateInput.setValue('2024-01-01')
    await nextTick()

    expect(wrapper.find('.detail-date-reset').exists()).toBe(true)

    await wrapper.find('.detail-date-reset').trigger('click')
    await nextTick()

    expect(wrapper.find('.detail-date-reset').exists()).toBe(false)
  })
})
