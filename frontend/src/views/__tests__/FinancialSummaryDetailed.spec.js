// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import FinancialSummaryDetailed from '../FinancialSummaryDetailed.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'

describe('FinancialSummaryDetailed', () => {
  const mountView = () =>
    shallowMount(FinancialSummaryDetailed, { global: { stubs: { BasePageLayout: false } } })

  it('starts on a real month-to-date range instead of empty strings', () => {
    const { startDate, endDate } = mountView().getComponent(DailyNetChart).props()
    expect(startDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(endDate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(startDate.endsWith('-01')).toBe(true)
    expect(endDate >= startDate).toBe(true)
  })

  it('date inputs drive both the chart and the summary', async () => {
    const wrapper = mountView()
    wrapper.getComponent(DateRangeSelector).vm.$emit('update:startDate', '2025-03-02')
    wrapper.getComponent(DateRangeSelector).vm.$emit('update:endDate', '2025-03-09')
    await wrapper.vm.$nextTick()
    expect(wrapper.getComponent(DailyNetChart).props()).toMatchObject({
      startDate: '2025-03-02',
      endDate: '2025-03-09',
    })
    expect(wrapper.findComponent({ name: 'FinancialSummary' }).props()).toMatchObject({
      startDate: '2025-03-02',
      endDate: '2025-03-09',
    })
  })
})
