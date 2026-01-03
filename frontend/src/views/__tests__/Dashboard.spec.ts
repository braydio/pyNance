// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick, watch, computed } from 'vue'
import Dashboard from '../Dashboard.vue'
import { fetchTransactions } from '@/api/transactions'

// Mock modules used by Dashboard.vue
vi.mock('@/services/api', () => ({
  default: { fetchNetAssets: vi.fn().mockResolvedValue({ status: 'success', data: [] }) },
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

vi.mock('@/composables/useDateRange', () => {
  const { ref, watch } = require('vue')

  function formatDateInput(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  function normalizeRange(range) {
    const startDate = new Date(range.start)
    const endDate = new Date(range.end)
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      return range
    }
    if (startDate > endDate) {
      return {
        start: formatDateInput(endDate),
        end: formatDateInput(startDate),
      }
    }
    return {
      start: formatDateInput(startDate),
      end: formatDateInput(endDate),
    }
  }

  return {
    useDateRange: (options = {}) => {
      const dateRange = ref({ start: '2024-02-01', end: '2024-02-29' })
      const debouncedRange = ref(normalizeRange(dateRange.value))
      const onChange = options.onDebouncedChange || (() => {})
      watch(
        dateRange,
        () => {
          const normalized = normalizeRange(dateRange.value)
          debouncedRange.value = normalized
          onChange(normalized)
        },
        { deep: true, immediate: true },
      )

      return {
        dateRange,
        debouncedRange,
        formatDateInput,
        getMonthBounds: () => ({
          start: new Date(dateRange.value.start),
          end: new Date(dateRange.value.end),
        }),
      }
    },
  }
})

const mockBreakdownType = ref<'category' | 'merchant'>('category')
const mockGroupOthers = ref(true)
const mockSelectedIds = ref<string[]>([])
const mockGroupedOptions = ref([
  {
    id: 'essentials',
    label: 'Essentials',
    children: [
      { id: 'groceries', label: 'Groceries' },
      { id: 'rent', label: 'Rent' },
    ],
  },
])
let autoSelected = false
const mockRefreshOptions = vi.fn(async () => {})
const mockLoadMerchantGroups = vi.fn(async () => {})
const mockResetSelection = vi.fn(() => {
  mockSelectedIds.value = []
  autoSelected = false
})
const mockSetBreakdownType = vi.fn((mode: 'category' | 'merchant') => {
  if (mockBreakdownType.value === mode) return
  mockBreakdownType.value = mode
  mockResetSelection()
})
const mockToggleGroupOthers = vi.fn(() => {
  mockGroupOthers.value = !mockGroupOthers.value
  autoSelected = false
})
const mockSetAvailableIds = vi.fn((ids: Array<string | number>) => {
  const normalized = (ids || []).map(String)
  if (!mockSelectedIds.value.length && normalized.length && !autoSelected) {
    mockSelectedIds.value = normalized.slice(0, 5)
    autoSelected = true
  }
})
const mockUpdateSelection = vi.fn((ids: string[] | string) => {
  mockSelectedIds.value = Array.isArray(ids) ? ids.map(String) : [String(ids)]
})

vi.mock('@/composables/useCategories', () => ({
  useCategories: () => ({
    breakdownType: mockBreakdownType,
    groupOthers: mockGroupOthers,
    selectedIds: mockSelectedIds,
    groupedOptions: computed(() => mockGroupedOptions.value),
    toggleGroupOthers: mockToggleGroupOthers,
    setAvailableIds: mockSetAvailableIds,
    updateSelection: mockUpdateSelection,
    resetSelection: mockResetSelection,
    setBreakdownType: mockSetBreakdownType,
    refreshOptions: mockRefreshOptions,
    loadMerchantGroups: mockLoadMerchantGroups,
  }),
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
const ChartWidgetTopBarStub = {
  name: 'ChartWidgetTopBar',
  template: '<div><slot name="controls" /></div>',
}
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
        groupOthers: props.groupOthers,
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
    ChartWidgetTopBar: ChartWidgetTopBarStub,
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
  fetchTransactions.mockClear()
  receivedProps = null
  dailyNetChartProps = null
  categoryChartProps = null
  autoSelected = false
  mockBreakdownType.value = 'category'
  mockGroupOthers.value = true
  mockSelectedIds.value = []
  mockRefreshOptions.mockClear()
  mockLoadMerchantGroups.mockClear()
  mockResetSelection.mockClear()
  mockSetBreakdownType.mockClear()
  mockToggleGroupOthers.mockClear()
  mockSetAvailableIds.mockClear()
  mockUpdateSelection.mockClear()
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
function formatDateInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

describe('Dashboard.vue', () => {
  it('defaults the date range to the current month boundaries', async () => {
    const wrapper = createWrapper()
    await nextTick()

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
    await nextTick()

    expect(receivedProps).not.toBeNull()
    expect(receivedProps.groups).toBeDefined()

    const chart = wrapper.findComponent(CategoryBreakdownChartStub)
    chart.vm.emitCategoriesChange(['a', 'b', 'c', 'd', 'e', 'f'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['a', 'b', 'c', 'd', 'e'])

    wrapper.vm.dateRange.start = '2024-01-01'
    wrapper.vm.dateRange.end = '2024-01-31'
    await vi.advanceTimersByTimeAsync(250)
    await nextTick()
    expect(mockSelectedIds.value).toEqual([])

    chart.vm.emitCategoriesChange(['x', 'y', 'z'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['x', 'y', 'z'])
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
    await vi.advanceTimersByTimeAsync(250)
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

  it('auto-selects top breakdown IDs when the chart emits category data', async () => {
    const wrapper = createWrapper()
    await nextTick()
    const chart = wrapper.findComponent(CategoryBreakdownChartStub)

    chart.vm.emitCategoriesChange(['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
    await nextTick()

    expect(mockSetAvailableIds).toHaveBeenCalledWith(['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
    expect(mockSelectedIds.value).toEqual(['c1', 'c2', 'c3', 'c4', 'c5'])

    mockResetSelection()
    chart.vm.emitCategoriesChange(['m1', 'm2'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['m1', 'm2'])
  })

  it('switches grouping mode when toggling consolidation controls', async () => {
    const wrapper = createWrapper()
    await nextTick()
    const toggleButton = wrapper
      .findAll('button')
      .find(
        (btn) =>
          btn.text().includes('Expand All') || btn.text().includes('Consolidate Minor Items'),
      )

    expect(toggleButton).toBeDefined()
    expect(toggleButton?.text()).toContain('Expand All')

    await toggleButton?.trigger('click')
    await nextTick()

    expect(mockToggleGroupOthers).toHaveBeenCalled()
    expect(mockGroupOthers.value).toBe(false)
    expect(categoryChartProps.groupOthers).toBe(false)
    expect(toggleButton?.text()).toContain('Consolidate Minor Items')
  })

  it('keeps overlays mutually exclusive between tables and modals', async () => {
    const wrapper = createWrapper()
    await nextTick()

    wrapper.vm.expandAccounts()
    await nextTick()
    expect(wrapper.vm.accountsExpanded).toBe(true)
    expect(wrapper.vm.transactionsExpanded).toBe(false)
    expect(wrapper.vm.showDailyModal).toBe(false)

    await wrapper.vm.onNetBarClick('2024-06-11')
    await nextTick()
    expect(wrapper.vm.accountsExpanded).toBe(false)
    expect(wrapper.vm.transactionsExpanded).toBe(false)
    expect(wrapper.vm.showDailyModal).toBe(true)

    wrapper.vm.expandTransactions()
    await nextTick()
    expect(wrapper.vm.transactionsExpanded).toBe(true)
    expect(wrapper.vm.showDailyModal).toBe(false)

    wrapper.vm.collapseTables()
    await nextTick()
    expect(wrapper.vm.accountsExpanded).toBe(false)
    expect(wrapper.vm.transactionsExpanded).toBe(false)
    expect(wrapper.vm.showDailyModal).toBe(false)
  })

  it('switches between transaction modals without overlapping overlays', async () => {
    const wrapper = createWrapper()
    await nextTick()

    await wrapper.vm.onNetBarClick('2024-06-12')
    await nextTick()
    expect(wrapper.vm.showDailyModal).toBe(true)
    expect(wrapper.vm.showCategoryModal).toBe(false)

    await wrapper.vm.onCategoryBarClick({ label: 'Food', ids: ['cat-1'] })
    await nextTick()
    expect(wrapper.vm.showDailyModal).toBe(false)
    expect(wrapper.vm.showCategoryModal).toBe(true)
  })
})
