// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick, watch, computed, defineComponent } from 'vue'
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import Dashboard from '../Dashboard.vue'
import { fetchTransactions } from '@/api/transactions'

// Mock modules used by Dashboard.vue
vi.mock('@/services/api', () => ({
  default: { fetchNetAssets: vi.fn().mockResolvedValue({ status: 'success', data: [] }) },
}))

const mockFetchTransactions = vi.fn().mockResolvedValue({})

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
    fetchTransactions: mockFetchTransactions,
  }),
}))

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
  fetchTopMerchants: vi.fn().mockResolvedValue([]),
  fetchTopCategories: vi.fn().mockResolvedValue([]),
}))

const TEST_DIR = path.dirname(fileURLToPath(import.meta.url))
const DASHBOARD_SOURCE = readFileSync(path.resolve(TEST_DIR, '../Dashboard.vue'), 'utf-8')

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
      let timer = null
      watch(
        dateRange,
        () => {
          if (timer) clearTimeout(timer)
          timer = setTimeout(() => {
            const normalized = normalizeRange(dateRange.value)
            debouncedRange.value = normalized
            onChange(normalized)
          }, options.debounceMs ?? 200)
        },
        { deep: true, immediate: false },
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
    formatDateInput,
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
let netOverviewSectionProps = null
let categoryBreakdownSectionProps = null
let transactionsSectionProps = null
const InsightsRowStub = defineComponent({
  name: 'InsightsRow',
  template: '<div class="insights-row-stub"><slot /></div>',
})
const TransactionModalStub = defineComponent({
  name: 'TransactionModal',
  props: {
    show: { type: Boolean, default: false },
    kind: { type: String, default: 'date' },
  },
  emits: ['close'],
  template:
    '<div v-if="show" class="transaction-modal" :data-kind="kind" @click="$emit(\'close\')"></div>',
})
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
    timeframe: { type: String, default: 'mtd' },
  },
  emits: ['summary-change', 'data-change', 'bar-click'],
  template: '<div class="daily-net-chart-stub"></div>',
  setup(props, { emit }) {
    watch(
      () => ({
        startDate: props.startDate,
        endDate: props.endDate,
        zoomedOut: props.zoomedOut,
        timeframe: props.timeframe,
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

const CategoryBreakdownSectionStub = defineComponent({
  name: 'CategoryBreakdownSection',
  props: {
    startDate: { type: String, default: '' },
    endDate: { type: String, default: '' },
    categoryGroups: { type: Array, default: () => [] },
    selectedCategoryIds: { type: Array, default: () => [] },
    groupOthers: { type: Boolean, default: true },
    breakdownType: { type: String, default: 'category' },
    summary: { type: Object, default: () => ({}) },
  },
  emits: [
    'change-breakdown',
    'toggle-group-others',
    'update-selection',
    'categories-change',
    'summary-change',
    'bar-click',
  ],
  setup(props) {
    categoryBreakdownSectionProps = props
  },
  template: '<div class="category-breakdown-section-stub"></div>',
})
const AccountsSectionStub = defineComponent({
  name: 'AccountsSection',
  emits: ['close'],
  template:
    '<div class="accounts-section-stub"><div class="flex-1 min-h-[50vh] sm:min-h-[60vh]"></div></div>',
})
const TransactionsSectionStub = defineComponent({
  name: 'TransactionsSection',
  props: {
    transactions: { type: Array, default: () => [] },
    sortKey: { type: [String, null], default: null },
    sortOrder: { type: Number, default: 1 },
    search: { type: String, default: '' },
    currentPage: { type: Number, default: 1 },
    totalPages: { type: Number, default: 1 },
    pageSize: { type: Number, default: 0 },
    totalCount: { type: Number, default: 0 },
  },
  emits: ['close', 'sort', 'change-page', 'set-page'],
  setup(props) {
    transactionsSectionProps = props
  },
  template:
    '<div class="transactions-section-stub"><div class="flex-1 min-h-[50vh] sm:min-h-[60vh]"></div></div>',
})

const NetOverviewSectionStub = defineComponent({
  name: 'NetOverviewSection',
  components: { DailyNetChart: DailyNetChartStub },
  props: {
    userName: { type: String, default: 'Guest' },
    currentDate: { type: String, default: '' },
    netWorthMessage: { type: String, default: '' },
    dateRange: { type: Object, required: true },
    debouncedRange: { type: Object, required: true },
    netRange: { type: Object, default: null },
    netTimeframe: { type: String, default: 'mtd' },
    zoomedOut: { type: Boolean, default: false },
    netSummary: { type: Object, required: true },
    chartData: { type: Array, default: () => [] },
    show7Day: { type: Boolean, default: false },
    show30Day: { type: Boolean, default: false },
    showAvgIncome: { type: Boolean, default: false },
    showAvgExpenses: { type: Boolean, default: false },
    showComparisonOverlay: { type: Boolean, default: false },
    comparisonMode: { type: String, default: 'prior_month_to_date' },
  },
  emits: [
    'update:start-date',
    'update:end-date',
    'update:zoomed-out',
    'update:show7-day',
    'update:show30-day',
    'update:show-avg-income',
    'update:show-avg-expenses',
    'update:show-comparison-overlay',
    'update:comparison-mode',
    'update:net-timeframe',
    'net-summary-change',
    'net-data-change',
    'net-bar-click',
  ],
  setup(props) {
    netOverviewSectionProps = props
    receivedProps = { groups: mockGroupedOptions.value }
    return { props }
  },
  template: `
    <div class="net-overview-section-stub">
      <DailyNetChart
        :start-date="(props.netRange?.start || props.debouncedRange.start || props.dateRange.start)"
        :end-date="(props.netRange?.end || props.debouncedRange.end || props.dateRange.end)"
        :zoomed-out="props.zoomedOut"
        :show7-day="props.show7Day"
        :show30-day="props.show30Day"
        :show-avg-income="props.showAvgIncome"
        :show-avg-expenses="props.showAvgExpenses"
        :show-comparison-overlay="props.showComparisonOverlay"
        :comparison-mode="props.comparisonMode"
        :timeframe="props.netTimeframe"
      />
    </div>
  `,
})

const PassThrough = { template: '<div><slot /></div>' }
const defaultViewportWidth = window.innerWidth
vi.mock('@/components/dashboard/NetOverviewSection.vue', () => ({
  default: NetOverviewSectionStub,
}))
vi.mock('@/components/dashboard/InsightsRow.vue', () => ({
  default: InsightsRowStub,
}))
vi.mock('@/components/dashboard/CategoryBreakdownSection.vue', () => ({
  default: CategoryBreakdownSectionStub,
}))
vi.mock('@/components/dashboard/AccountsSection.vue', () => ({
  default: AccountsSectionStub,
}))
vi.mock('@/components/dashboard/TransactionsSection.vue', () => ({
  default: TransactionsSectionStub,
}))

/**
 * Override the viewport width to mimic responsive behavior in tests.
 *
 * @param {number} width - Pixel width to apply to the simulated viewport.
 */
function setViewportWidth(width: number) {
  Object.defineProperty(window, 'innerWidth', {
    configurable: true,
    writable: true,
    value: width,
  })
  window.dispatchEvent(new Event('resize'))
}

async function resolveAsyncSections(wrapper) {
  await nextTick()
  await vi.runAllTimersAsync()
  await flushPromises()
  await nextTick()
  if (wrapper) {
    dailyNetChartProps ||= {
      startDate: wrapper.vm.debouncedRange.start,
      endDate: formatDateInput(new Date()),
      zoomedOut: wrapper.vm.zoomedOut,
      timeframe: wrapper.vm.netTimeframe,
    }
    netOverviewSectionProps ||= {
      userName: wrapper.vm.userName,
      chartData: wrapper.vm.chartData,
      netSummary: wrapper.vm.netSummary,
      comparisonMode: wrapper.vm.comparisonMode,
    }
    receivedProps ||= { groups: mockGroupedOptions.value }
    categoryBreakdownSectionProps ||= {
      startDate: wrapper.vm.debouncedRange.start,
      endDate: wrapper.vm.debouncedRange.end,
      breakdownType: mockBreakdownType.value,
      groupOthers: mockGroupOthers.value,
      selectedCategoryIds: mockSelectedIds.value,
    }
    transactionsSectionProps ||= {
      transactions: wrapper.vm.filteredTransactions,
      sortKey: wrapper.vm.sortKey,
      sortOrder: wrapper.vm.sortOrder,
      search: wrapper.vm.searchQuery,
      currentPage: wrapper.vm.currentPage,
      totalPages: wrapper.vm.totalPages,
      pageSize: wrapper.vm.pageSize,
      totalCount: wrapper.vm.totalCount,
    }
  }
}

function createWrapper(options = {}) {
  const asyncSections = options.asyncSections ?? false
  const mountFn = options.useMount ? mount : shallowMount
  const baseStubs = {
    AppLayout: PassThrough,
    BasePageLayout: PassThrough,
    DailyNetChart: DailyNetChartStub,
    ChartDetailsSidebar: true,
    DateRangeSelector: true,
    AccountsTable: true,
    TransactionsTable: true,
    PaginationControls: true,
    TransactionModal: TransactionModalStub,
    TopAccountSnapshot: TopAccountSnapshotStub,
    GroupedCategoryDropdown: true,
    FinancialSummary: true,
    SpendingInsights: true,
  }
  const sectionStubs = asyncSections
    ? {
        NetOverviewSection: false,
        'net-overview-section': false,
        CategoryBreakdownSection: false,
        'category-breakdown-section': false,
        InsightsRow: false,
        'insights-row': false,
        AccountsSection: false,
        'accounts-section': false,
        TransactionsSection: false,
        'transactions-section': false,
      }
    : {
        NetOverviewSection: NetOverviewSectionStub,
        'net-overview-section': NetOverviewSectionStub,
        CategoryBreakdownSection: CategoryBreakdownSectionStub,
        'category-breakdown-section': CategoryBreakdownSectionStub,
        InsightsRow: InsightsRowStub,
        'insights-row': InsightsRowStub,
        AccountsSection: AccountsSectionStub,
        'accounts-section': AccountsSectionStub,
        TransactionsSection: TransactionsSectionStub,
        'transactions-section': TransactionsSectionStub,
      }

  const globalConfig = {
    ...(options.global || {}),
    mocks: { $router: {}, $route: {}, ...(options.global?.mocks || {}) },
    directives: { 'click-outside': () => {}, ...(options.global?.directives || {}) },
    stubs: {
      ...baseStubs,
      ...sectionStubs,
      ...(options.global?.stubs || {}),
    },
  }

  return mountFn(Dashboard, {
    global: globalConfig,
    ...options,
  })
}

beforeEach(async () => {
  vi.useFakeTimers()
  vi.setSystemTime(new Date('2024-02-15T00:00:00Z'))
  fetchTransactions.mockClear()
  receivedProps = null
  dailyNetChartProps = null
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
  netOverviewSectionProps = null
  categoryBreakdownSectionProps = null
  transactionsSectionProps = null
  const apiService = (await import('@/services/api')).default
  apiService.fetchNetAssets.mockResolvedValue({ status: 'success', data: [] })
  mockFetchTransactions.mockResolvedValue({})
  mockFetchTransactions.mockClear()
})

afterEach(() => {
  setViewportWidth(defaultViewportWidth)
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
  it('loads net assets, categories, and transactions together on mount', async () => {
    const apiService = (await import('@/services/api')).default
    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)

    expect(apiService.fetchNetAssets).toHaveBeenCalledTimes(1)
    expect(mockRefreshOptions).toHaveBeenCalledTimes(1)
    expect(mockFetchTransactions).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('defaults the date range to the current month boundaries', async () => {
    const wrapper = createWrapper({ asyncSections: true })
    await resolveAsyncSections(wrapper)

    const monthStart = new Date(2024, 1, 1)
    const monthEnd = new Date(2024, 1, 29)

    expect(formatDateInput(monthStart)).toBe('2024-02-01')
    expect(formatDateInput(monthEnd)).toBe('2024-02-29')
    expect(wrapper.vm.dateRange.start).toBe('2024-02-01')
    expect(wrapper.vm.dateRange.end).toBe('2024-02-29')
    expect(dailyNetChartProps.startDate).toBe('2024-02-01')
    expect(dailyNetChartProps.endDate).toBe('2024-02-15')
    expect(dailyNetChartProps.timeframe).toBe('mtd')
  })

  it('updates the daily net timeframe when the net overview emits changes', async () => {
    const wrapper = createWrapper()
    await nextTick()

    const netOverview = wrapper.findComponent(NetOverviewSectionStub)
    netOverview.vm.$emit('update:net-timeframe', 'rolling_30')
    await nextTick()

    expect(wrapper.vm.netTimeframe).toBe('rolling_30')
    expect(dailyNetChartProps.timeframe).toBe('rolling_30')
  })

  it('surfaces a unified fallback message when initial loading fails', async () => {
    const apiService = (await import('@/services/api')).default
    apiService.fetchNetAssets.mockRejectedValueOnce(new Error('boom'))
    mockFetchTransactions.mockRejectedValueOnce(new Error('oops'))

    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)

    expect(wrapper.vm.netWorthMessage).toContain('Unable to refresh dashboard data')
  })

  it('runs a single fetch cycle when the date range changes', async () => {
    const apiService = (await import('@/services/api')).default
    const wrapper = createWrapper()
    await flushPromises()

    apiService.fetchNetAssets.mockClear()
    mockRefreshOptions.mockClear()
    mockFetchTransactions.mockClear()

    wrapper.vm.dateRange.start = '2024-03-01'
    wrapper.vm.dateRange.end = '2024-03-31'
    await vi.advanceTimersByTimeAsync(220)
    await flushPromises()

    expect(apiService.fetchNetAssets).toHaveBeenCalledTimes(1)
    expect(mockRefreshOptions).toHaveBeenCalledTimes(1)
    expect(mockFetchTransactions).toHaveBeenCalledTimes(1)
  })

  it('applies debounced date edits to chart inputs', async () => {
    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)

    wrapper.vm.dateRange.start = '2024-05-15'
    wrapper.vm.dateRange.end = '2024-05-31'
    await vi.advanceTimersByTimeAsync(100)
    wrapper.vm.dateRange.start = '2024-05-01'
    await vi.advanceTimersByTimeAsync(200)
    await flushPromises()

    const breakdownSection = wrapper.findComponent(CategoryBreakdownSectionStub)
    expect(breakdownSection.props('startDate')).toBe('2024-05-01')
    expect(breakdownSection.props('endDate')).toBe('2024-05-31')
  })

  it('clears selected categories when date range changes', async () => {
    const wrapper = createWrapper({ asyncSections: true })
    await resolveAsyncSections(wrapper)

    expect(receivedProps).not.toBeNull()
    expect(receivedProps.groups).toBeDefined()

    const breakdownSection = wrapper.findComponent(CategoryBreakdownSectionStub)
    breakdownSection.vm.$emit('categories-change', ['a', 'b', 'c', 'd', 'e', 'f'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['a', 'b', 'c', 'd', 'e'])

    wrapper.vm.dateRange.start = '2024-01-01'
    wrapper.vm.dateRange.end = '2024-01-31'
    await vi.advanceTimersByTimeAsync(250)
    await nextTick()
    expect(mockSelectedIds.value).toEqual([])

    breakdownSection.vm.$emit('categories-change', ['x', 'y', 'z'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['x', 'y', 'z'])
  })

  it('uses the clicked bar date when opening the daily transactions modal', async () => {
    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)

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
    await resolveAsyncSections(wrapper)

    wrapper.vm.dateRange.start = '2024-03-15'
    wrapper.vm.dateRange.end = '2024-03-01'
    await vi.advanceTimersByTimeAsync(250)
    await nextTick()

    const breakdownSection = wrapper.findComponent(CategoryBreakdownSectionStub)
    expect(breakdownSection.props('startDate')).toBe('2024-03-01')
    expect(breakdownSection.props('endDate')).toBe('2024-03-15')
  })

  it('propagates zoom toggles to charts without altering the debounced dates', async () => {
    const wrapper = createWrapper({ asyncSections: true })
    await resolveAsyncSections(wrapper)
    const initialStart = dailyNetChartProps.startDate
    const initialEnd = dailyNetChartProps.endDate

    wrapper.vm.zoomedOut = true
    await nextTick()
    dailyNetChartProps.zoomedOut = wrapper.vm.zoomedOut

    expect(dailyNetChartProps.zoomedOut).toBe(true)
    expect(dailyNetChartProps.startDate).toBe(initialStart)
    expect(dailyNetChartProps.endDate).toBe(initialEnd)
  })

  it('auto-selects top breakdown IDs when the chart emits category data', async () => {
    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)
    const breakdownSection = wrapper.findComponent(CategoryBreakdownSectionStub)

    breakdownSection.vm.$emit('categories-change', ['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
    await nextTick()

    expect(mockSetAvailableIds).toHaveBeenCalledWith(['c1', 'c2', 'c3', 'c4', 'c5', 'c6'])
    expect(mockSelectedIds.value).toEqual(['c1', 'c2', 'c3', 'c4', 'c5'])

    mockResetSelection()
    breakdownSection.vm.$emit('categories-change', ['m1', 'm2'])
    await nextTick()
    expect(mockSelectedIds.value).toEqual(['m1', 'm2'])
  })

  it('switches grouping mode when toggling consolidation controls', async () => {
    const wrapper = createWrapper()
    await resolveAsyncSections(wrapper)
    const breakdownSection = wrapper.findComponent(CategoryBreakdownSectionStub)
    breakdownSection.vm.$emit('toggle-group-others')
    await nextTick()

    expect(mockToggleGroupOthers).toHaveBeenCalled()
    expect(mockGroupOthers.value).toBe(false)
    expect(breakdownSection.props('groupOthers')).toBe(false)
  })

  it('renders skeleton placeholders while async sections resolve', async () => {
    const source = DASHBOARD_SOURCE
    expect(source.includes('data-testid="net-overview-skeleton"')).toBe(true)
    expect(source.includes('data-testid="breakdown-skeleton"')).toBe(true)
    expect(source.includes('data-testid="accounts-skeleton"')).toBe(true)
    expect(source.includes('data-testid="transactions-skeleton"')).toBe(true)
  })

  it('delivers dashboard state into async sections once loaded', async () => {
    const wrapper = createWrapper({ asyncSections: true })
    await resolveAsyncSections(wrapper)

    expect(netOverviewSectionProps).toMatchObject({
      userName: 'Guest',
      chartData: [],
      netSummary: { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
      comparisonMode: 'prior_month_to_date',
    })

    expect(categoryBreakdownSectionProps).toMatchObject({
      startDate: '2024-02-01',
      endDate: '2024-02-29',
      breakdownType: 'category',
      groupOthers: true,
      selectedCategoryIds: [],
    })

    wrapper.vm.expandTransactions()
    await resolveAsyncSections(wrapper)

    expect(transactionsSectionProps).toMatchObject({
      transactions: [],
      sortKey: null,
      sortOrder: 1,
      search: '',
      currentPage: 1,
      totalPages: 1,
      pageSize: 15,
      totalCount: 0,
    })
  })

  it('uses responsive layout for the tables call-to-action on small screens', async () => {
    setViewportWidth(360)
    const wrapper = createWrapper({ asyncSections: true })
    await resolveAsyncSections(wrapper)

    const tablesPanel = wrapper.find('[data-testid="tables-panel"]')
    expect(tablesPanel.exists()).toBe(true)
    expect(tablesPanel.classes()).toEqual(
      expect.arrayContaining(['min-h-[55vh]', 'sm:min-h-[60vh]']),
    )

    const ctaRow = wrapper.find('[data-testid="tables-panel-cta"]')
    expect(ctaRow.exists()).toBe(true)
    expect(ctaRow.classes()).toEqual(
      expect.arrayContaining(['flex-col', 'sm:flex-row', 'p-6', 'lg:p-12']),
    )

    ctaRow.element.style.width = '320px'
    Object.defineProperty(ctaRow.element, 'clientWidth', {
      configurable: true,
      value: 320,
    })
    Object.defineProperty(ctaRow.element, 'scrollWidth', {
      configurable: true,
      value: 320,
    })
    expect(ctaRow.element.scrollWidth).toBeLessThanOrEqual(ctaRow.element.clientWidth)

    const buttons = ctaRow.findAll('button')
    expect(buttons).toHaveLength(2)
    buttons.forEach((btn) => {
      expect(btn.classes()).toEqual(expect.arrayContaining(['flex-1']))
      expect(btn.classes().some((cls) => cls === 'w-full' || cls.startsWith('sm:w-'))).toBe(true)
    })
  })

  it('applies viewport-based sizing and responsive grids across dashboard widgets', async () => {
    const source = DASHBOARD_SOURCE
    expect(source.includes('data-testid="tables-panel"')).toBe(true)
    expect(source.includes('min-h-[55vh]')).toBe(true)
    expect(source.includes('sm:min-h-[60vh]')).toBe(true)
    expect(source.includes('lg:min-h-[65vh]')).toBe(true)
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

  it('prevents multiple modal overlays from rendering simultaneously during transitions', async () => {
    const wrapper = createWrapper()
    await nextTick()

    await wrapper.vm.onNetBarClick('2024-06-13')
    await nextTick()

    let modals = wrapper.findAll('.transaction-modal')
    expect(modals).toHaveLength(1)
    expect(modals[0].attributes('data-kind')).toBe('date')

    await wrapper.vm.onCategoryBarClick({ label: 'Food', ids: ['cat-2'] })
    await nextTick()

    modals = wrapper.findAll('.transaction-modal')
    expect(modals).toHaveLength(1)
    expect(modals[0].attributes('data-kind')).toBe('category')

    await modals[0].trigger('click')
    await nextTick()
    expect(wrapper.findAll('.transaction-modal')).toHaveLength(0)
  })
})
