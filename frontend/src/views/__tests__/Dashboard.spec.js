// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Dashboard from '../Dashboard.vue'
import { fetchTransactions } from '@/api/transactions'

// Mock modules used by Dashboard.vue
vi.mock('@/services/api', () => ({
  default: { fetchNetAssets: vi.fn().mockResolvedValue({ status: 'success', data: [] }) },
}))

vi.mock('@/api/categories', () => ({
  fetchCategoryTree: vi.fn().mockResolvedValue({ status: 'success', data: [] }),
}))

vi.mock('@/composables/useTransactions.js', () => ({
  useTransactions: () => ({
    searchQuery: ref(''),
    currentPage: ref(1),
    totalPages: ref(1),
    totalCount: ref(0),
    filteredTransactions: ref([]),
    sortKey: ref(null),
    sortOrder: ref(1),
    setSort: vi.fn(),
    setPage: vi.fn(),
    changePage: vi.fn(),
  }),
}))

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
}))

vi.mock('@/composables/useAccountGroups', () => ({
  useAccountGroups: () => ({ groups: ref([]), activeGroupId: ref(null) }),
}))

let receivedProps = null
const TopAccountSnapshotStub = {
  name: 'TopAccountSnapshot',
  template: '<div class="tas-stub"></div>',
  props: {
    groups: { type: Array, default: () => [] },
    modelValue: { type: Array, default: () => [] },
  },
  setup(props) {
    receivedProps = props
  },
}

const DailyNetChartStub = {
  name: 'DailyNetChart',
  props: [
    'startDate',
    'endDate',
    'displayStartDate',
    'displayEndDate',
    'rangeMode',
    'zoomedOut',
  ],
  emits: ['summary-change', 'data-change', 'bar-click'],
  template: '<div class="daily-net-chart-stub"></div>',
}

const PassThrough = { template: '<div><slot /></div>' }

// Tests for Dashboard.vue date range behavior

/**
 * Format a Date instance as YYYY-MM-DD for dashboard assertions.
 *
 * @param {Date} date - Date to format.
 * @returns {string} Date string in YYYY-MM-DD format.
 */
function formatDateInput(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

describe('Dashboard.vue', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2024-06-18T12:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('defaults the date range to the current month', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: DailyNetChartStub,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    const today = new Date('2024-06-18T12:00:00Z')
    const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)

    expect(wrapper.vm.dateRange.start).toBe(formatDateInput(monthStart))
    expect(wrapper.vm.dateRange.end).toBe(formatDateInput(today))
  })

  it('switches between month-to-date and rolling 30 day ranges', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: DailyNetChartStub,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    const chart = wrapper.findComponent(DailyNetChartStub)
    expect(chart.props('startDate')).toBe('2024-06-01')
    expect(chart.props('endDate')).toBe('2024-06-18')
    expect(chart.props('displayEndDate')).toBe('2024-06-30')
    expect(chart.props('rangeMode')).toBe('month_to_date')

    await wrapper.find('[data-testid="daily-net-range-rolling"]').trigger('click')
    await nextTick()

    const rollingChart = wrapper.findComponent(DailyNetChartStub)
    expect(rollingChart.props('startDate')).toBe('2024-05-19')
    expect(rollingChart.props('endDate')).toBe('2024-06-18')
    expect(rollingChart.props('displayEndDate')).toBe('2024-06-18')
    expect(rollingChart.props('rangeMode')).toBe('last_30_days')

    await wrapper.find('[data-testid="daily-net-range-month"]').trigger('click')
    await nextTick()

    const monthlyChart = wrapper.findComponent(DailyNetChartStub)
    expect(monthlyChart.props('startDate')).toBe('2024-06-01')
    expect(monthlyChart.props('endDate')).toBe('2024-06-18')
    expect(monthlyChart.props('displayEndDate')).toBe('2024-06-30')
    expect(monthlyChart.props('rangeMode')).toBe('month_to_date')
  })

  it('clears selected categories when date range changes', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: DailyNetChartStub,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    expect(receivedProps).not.toBeNull()
    expect(receivedProps.groups).toBeDefined()

    wrapper.vm.allCategoryIds = ['a', 'b', 'c', 'd', 'e', 'f']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['a', 'b', 'c', 'd', 'e'])

    wrapper.vm.dateRange.start = '2024-01-01'
    wrapper.vm.dateRange.end = '2024-01-31'
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual([])

    wrapper.vm.allCategoryIds = ['x', 'y', 'z']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['x', 'y', 'z'])
  })

  it('uses the clicked bar date when opening the daily transactions modal', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: true,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    const barLabel = '2024-06-10T00:00:00'
    await wrapper.vm.onNetBarClick(barLabel)

    expect(fetchTransactions).toHaveBeenCalledWith({
      start_date: '2024-06-10',
      end_date: '2024-06-10',
      page: 1,
      page_size: 1000,
    })
    expect(wrapper.vm.dailyModalSubtitle).toBe('2024-06-10')
    expect(wrapper.vm.showDailyModal).toBe(true)
  })
})
