// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
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

    await wrapper.find('.stats-toggle-btn').trigger('click')
    const html = wrapper.html()
    expect(html).toContain('Income Trend')
    expect(html).toContain('+$100.00')
    expect(html).toContain('Expense Trend')
    expect(html).toContain('+$100.00')
  })
})
