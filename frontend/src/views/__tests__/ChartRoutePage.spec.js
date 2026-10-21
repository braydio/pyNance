// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import ChartRoutePage from '../ChartRoutePage.vue'
import DailyNetChart from '@/components/charts/DailyNetChart.vue'
import CategoryBreakdownChart from '@/components/charts/CategoryBreakdownChart.vue'
import NetYearComparisonChart from '@/components/charts/NetYearComparisonChart.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import ChartRangePresets from '@/components/charts/ChartRangePresets.vue'
import router from '@/router'

const refreshOptions = vi.hoisted(() => vi.fn())
const routeState = vi.hoisted(() => ({ query: {} }))
vi.mock('vue-router', async (importOriginal) => ({
  ...(await importOriginal()),
  useRoute: () => routeState,
}))
vi.mock('@/composables/useCategories', () => ({
  useCategories: () => ({
    groupedOptions: ref([{ id: 'g', label: 'Food', children: [{ id: '1', label: 'Groceries' }] }]),
    selectedIds: ref(['1']),
    groupOthers: ref(true),
    setAvailableIds: vi.fn(),
    updateSelection: vi.fn(),
    refreshOptions,
  }),
}))

const ISO = /^\d{4}-\d{2}-\d{2}$/

function mountPage(variant) {
  return shallowMount(ChartRoutePage, {
    props: { variant },
    global: { stubs: { BasePageLayout: false, PageHeader: false } },
  })
}

describe('ChartRoutePage', () => {
  beforeEach(() => {
    refreshOptions.mockClear()
    routeState.query = {}
  })

  it('passes real month-to-date local dates to the cashflow chart', () => {
    const wrapper = mountPage('cashflow')
    const chart = wrapper.getComponent(DailyNetChart)
    const { startDate, endDate } = chart.props()
    expect(startDate).toMatch(ISO)
    expect(endDate).toMatch(ISO)
    expect(startDate.endsWith('-01')).toBe(true)
    expect(startDate <= endDate).toBe(true)
    expect(wrapper.text()).toContain('Cash Flow')
    expect(wrapper.get('[data-testid="chart-route-period"]').text()).toContain(startDate)
  })

  it('passes the selected preset to the cashflow chart so buckets follow it', async () => {
    const wrapper = mountPage('cashflow')
    expect(wrapper.getComponent(DailyNetChart).props('timeframe')).toBe('mtd')
    wrapper.getComponent(ChartRangePresets).vm.$emit('update:modelValue', 'ytd')
    await flushPromises()
    const chart = wrapper.getComponent(DailyNetChart)
    expect(chart.props('timeframe')).toBe('ytd')
    expect(chart.props('startDate').endsWith('-01-01')).toBe(true)
  })

  it('treats start_date/end_date deep links as a custom range', () => {
    routeState.query = { start_date: '2026-01-05', end_date: '2026-09-30' }
    const chart = mountPage('cashflow').getComponent(DailyNetChart)
    expect(chart.props()).toMatchObject({
      startDate: '2026-01-05',
      endDate: '2026-09-30',
      timeframe: 'custom',
    })
  })

  it('date inputs change the chart range', async () => {
    const wrapper = mountPage('cashflow')
    const selector = wrapper.getComponent(DateRangeSelector)
    selector.vm.$emit('update:start-date', '2025-01-08')
    selector.vm.$emit('update:end-date', '2025-01-17')
    await flushPromises()
    expect(wrapper.getComponent(DailyNetChart).props()).toMatchObject({
      startDate: '2025-01-08',
      endDate: '2025-01-17',
    })
  })

  it('supplies dates, selected categories and options to the category chart', async () => {
    const wrapper = mountPage('category')
    await flushPromises()
    const chart = wrapper.getComponent(CategoryBreakdownChart)
    expect(chart.props('startDate')).toMatch(ISO)
    expect(chart.props('endDate')).toMatch(ISO)
    expect(chart.props('selectedCategoryIds')).toEqual(['1'])
    expect(refreshOptions).toHaveBeenCalledWith({
      start_date: chart.props('startDate'),
      end_date: chart.props('endDate'),
    })
    expect(wrapper.text()).toContain('Spending by Category')
  })

  it('shows the year comparison without a date picker', () => {
    const wrapper = mountPage('year')
    expect(wrapper.findComponent(NetYearComparisonChart).exists()).toBe(true)
    expect(wrapper.findComponent(DateRangeSelector).exists()).toBe(false)
    expect(wrapper.text()).toContain('Year Comparison')
  })

  it('keeps the original chart URLs and route names', () => {
    const byPath = Object.fromEntries(router.getRoutes().map((r) => [r.path, r]))
    expect(byPath['/charts/cashflow'].name).toBe('DailyNetChart')
    expect(byPath['/charts/category'].name).toBe('CategoryChart')
    expect(byPath['/charts/assets/year-comparison'].name).toBe('NetYearComparisonChart')
    expect(byPath['/charts/cashflow'].props.default).toEqual({ variant: 'cashflow' })
    expect(byPath['/charts/category'].props.default).toEqual({ variant: 'category' })
    expect(byPath['/charts/assets/year-comparison'].props.default).toEqual({ variant: 'year' })
  })

  it('defaults the cash flow chart to cash movement and lets the user pick economic activity', async () => {
    const wrapper = mountPage('cashflow')
    expect(wrapper.getComponent(DailyNetChart).props('basis')).toBe('cash')
    await wrapper.get('[data-testid="chart-route-basis-economic"]').trigger('click')
    expect(wrapper.getComponent(DailyNetChart).props('basis')).toBe('economic')
  })
})

