// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick, watch } from 'vue'
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

let dailyNetChartProps = null
const DailyNetChartStub = {
  name: 'DailyNetChart',
  props: {
    startDate: { type: String, required: true },
    endDate: { type: String, required: true },
    zoomedOut: { type: Boolean, default: false },
    show7Day: { type: Boolean, default: false },
    show30Day: { type: Boolean, default: false },
    showAvgIncome: { type: Boolean, default: false },
    showAvgExpenses: { type: Boolean, default: false },
    showComparisonOverlay: { type: Boolean, default: false },
    comparisonMode: { type: String, default: 'prior_month_to_date' },
  },
  emits: ['summary-change', 'data-change', 'bar-click'],
  template: '<div class="daily-net-chart-stub"></div>',
  setup(props, { emit }) {
    watch(
      () => ({
        startDate: props.startDate,
        endDate: props.endDate,
        zoomedOut: props.zoomedOut,
      }),
      (val) => {
        dailyNetChartProps = val
      },
      { immediate: true },
    )

    return {
      emitBarClick: (payload) => emit('bar-click', payload),
    }
  },
}

let categoryChartProps = null
const CategoryBreakdownChartStub = {
  name: 'CategoryBreakdownChart',
  props: {
    startDate: { type: String, required: true },
    endDate: { type: String, required: true },
    selectedCategoryIds: { type: Array, default: () => [] },
    groupOthers: { type: Boolean, default: true },
    breakdownType: { type: String, default: 'category' },
  },
  emits: ['bar-click', 'summary-change', 'categories-change'],
  template: '<div class="category-breakdown-stub"></div>',
  setup(props, { emit }) {
    watch(
      () => ({
        startDate: props.startDate,
        endDate: props.endDate,
        breakdownType: props.breakdownType,
      }),
      (val) => {
        categoryChartProps = val
      },
      { immediate: true },
    )

    return {
      emitSummaryChange: (payload) => emit('summary-change', payload),
      emitCategoriesChange: (payload) => emit('categories-change', payload),
    }
  },
}

const PassThrough = { template: '<div><slot /></div>' }

function createWrapper(options = {}) {
  const baseStubs = {
    AppLayout: PassThrough,
    BasePageLayout: PassThrough,
    DailyNetChart: DailyNetChartStub,
    CategoryBreakdownChart: CategoryBreakdownChartStub,
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
  }

  return shallowMount(Dashboard, {
    global: {
      ...(options.global || {}),
      stubs: {
        ...baseStubs,
        ...(options.global?.stubs || {}),
      },
    },
    ...options,
  })
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2024-02-15T00:00:00Z'))
  receivedProps = null
  dailyNetChartProps = null
  categoryChartProps = null
})

afterEach(() => {
  vi.useRealTimers()
})

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
  it('defaults the date range to the current month boundaries', async () => {
    const wrapper = createWrapper()

    const monthStart = new Date(2024, 1, 1)
    const monthEnd = new Date(2024, 1, 29)

    expect(formatDateInput(monthStart)).toBe('2024-02-01')
    expect(formatDateInput(monthEnd)).toBe('2024-02-29')
    expect(wrapper.vm.dateRange.start).toBe('2024-02-01')
    expect(wrapper.vm.dateRange.end).toBe('2024-02-29')
    expect(dailyNetChartProps.startDate).toBe(formatDateInput(monthStart))
    expect(dailyNetChartProps.endDate).toBe(formatDateInput(monthEnd))
  })

  it('clears selected categories when date range changes', async () => {
    const wrapper = createWrapper()

    expect(receivedProps).not.toBeNull()
    expect(receivedProps.groups).toBeDefined()

    wrapper.vm.allCategoryIds = ['a', 'b', 'c', 'd', 'e', 'f']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['a', 'b', 'c', 'd', 'e'])

    wrapper.vm.dateRange.start = '2024-01-01'
    wrapper.vm.dateRange.end = '2024-01-31'
    await vi.runAllTimersAsync()
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual([])

    wrapper.vm.allCategoryIds = ['x', 'y', 'z']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['x', 'y', 'z'])
  })

  it('uses the clicked bar date when opening the daily transactions modal', async () => {
    const wrapper = createWrapper()

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

  it('normalizes reversed date inputs before notifying charts', async () => {
    const wrapper = createWrapper()

    wrapper.vm.dateRange.start = '2024-03-15'
    wrapper.vm.dateRange.end = '2024-03-01'
    await vi.runAllTimersAsync()
    await nextTick()

    expect(dailyNetChartProps.startDate).toBe('2024-03-01')
    expect(dailyNetChartProps.endDate).toBe('2024-03-15')
    expect(categoryChartProps.startDate).toBe('2024-03-01')
    expect(categoryChartProps.endDate).toBe('2024-03-15')
  })

  it('propagates zoom toggles to charts without altering the debounced dates', async () => {
    const wrapper = createWrapper()
    const initialStart = dailyNetChartProps.startDate
    const initialEnd = dailyNetChartProps.endDate

    wrapper.vm.zoomedOut = true
    await nextTick()

    expect(dailyNetChartProps.zoomedOut).toBe(true)
    expect(dailyNetChartProps.startDate).toBe(initialStart)
    expect(dailyNetChartProps.endDate).toBe(initialEnd)
  })
})
