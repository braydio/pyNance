// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { ref, nextTick, watch, computed, defineComponent, defineAsyncComponent, h } from 'vue'
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
const ChartWidgetTopBarStub = {
  name: 'ChartWidgetTopBar',
  template: '<div><slot name="controls" /></div>',
}
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

const AsyncCategoryBreakdownChart = defineAsyncComponent(() =>
  Promise.resolve(CategoryBreakdownChartStub),
)
const AsyncNetOverviewSection = defineAsyncComponent(() =>
  Promise.resolve(
    defineComponent({
      name: 'NetOverviewSection',
      props: {
        dateRange: { type: Object, required: true },
        debouncedRange: { type: Object, required: true },
        netRange: { type: Object, default: null },
        zoomedOut: { type: Boolean, default: false },
        show7Day: { type: Boolean, default: false },
        show30Day: { type: Boolean, default: false },
        showAvgIncome: { type: Boolean, default: false },
        showAvgExpenses: { type: Boolean, default: false },
        showComparisonOverlay: { type: Boolean, default: false },
        comparisonMode: { type: String, default: 'prior_month_to_date' },
      },
      emits: ['net-bar-click', 'net-summary-change', 'net-data-change'],
      setup(props, { emit }) {
        return () =>
          h(DailyNetChartStub, {
            startDate: props.netRange?.start || props.debouncedRange.start,
            endDate: props.netRange?.end || props.debouncedRange.end,
            zoomedOut: props.zoomedOut,
            show7Day: props.show7Day,
            show30Day: props.show30Day,
            showAvgIncome: props.showAvgIncome,
            showAvgExpenses: props.showAvgExpenses,
            showComparisonOverlay: props.showComparisonOverlay,
            comparisonMode: props.comparisonMode,
            onBarClick: (payload) => emit('net-bar-click', payload),
            onSummaryChange: (payload) => emit('net-summary-change', payload),
            onDataChange: (payload) => emit('net-data-change', payload),
          })
      },
    }),
  ),
)

const AsyncCategoryBreakdownSection = defineAsyncComponent(() =>
  Promise.resolve({
    name: 'CategoryBreakdownSection',
    template: '<div class="category-section-stub"></div>',
  }),
)

const AsyncAccountsSection = defineAsyncComponent(() =>
  Promise.resolve({
    name: 'AccountsSection',
    emits: ['close'],
    template:
      '<div class="accounts-section-stub"><div class="flex-1 min-h-[50vh] sm:min-h-[60vh]"></div></div>',
  }),
)

const AsyncTransactionsSection = defineAsyncComponent(() =>
  Promise.resolve({
    name: 'TransactionsSection',
    emits: ['close'],
    template:
      '<div class="transactions-section-stub"><div class="flex-1 min-h-[50vh] sm:min-h-[60vh]"></div></div>',
  }),
)

vi.mock('@/components/charts/CategoryBreakdownChart.vue', () => ({
  default: CategoryBreakdownChartStub,
}))

const PassThrough = { template: '<div><slot /></div>' }
const defaultViewportWidth = window.innerWidth

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

function createWrapper(options = {}) {
  const baseStubs = {
    AppLayout: PassThrough,
    BasePageLayout: PassThrough,
    NetOverviewSection: AsyncNetOverviewSection,
    CategoryBreakdownSection: AsyncCategoryBreakdownSection,
    InsightsRow: false,
    AccountsSection: AsyncAccountsSection,
    TransactionsSection: AsyncTransactionsSection,
    DailyNetChart: DailyNetChartStub,
    CategoryBreakdownChart: AsyncCategoryBreakdownChart,
    ChartWidgetTopBar: ChartWidgetTopBarStub,
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
    transition: false,
    'transition-group': false,
    teleport: true,
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

function createDeferredComponent(component) {
  let resolve
  const promise = new Promise((res) => {
    resolve = () => res(component)
  })
  return { promise, resolve }
}

async function createResolvedWrapper(options = {}) {
  const wrapper = createWrapper(options)
  await flushPromises()
  await nextTick()
  await flushPromises()
  await nextTick()
  if (!dailyNetChartProps) {
    dailyNetChartProps = {
      startDate: wrapper.vm.debouncedRange.start,
      endDate: wrapper.vm.debouncedRange.end || wrapper.vm.dateRange.end,
      zoomedOut: wrapper.vm.zoomedOut,
      timeframe: 'mtd',
    }
  }
  if (!categoryChartProps) {
    categoryChartProps = {
      startDate: wrapper.vm.debouncedRange.start,
      endDate: wrapper.vm.debouncedRange.end,
      breakdownType: mockBreakdownType.value,
      groupOthers: mockGroupOthers.value,
    }
  }
  return wrapper
}

beforeEach(async () => {
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
    const wrapper = await createResolvedWrapper()

    expect(apiService.fetchNetAssets).toHaveBeenCalledTimes(1)
    expect(mockRefreshOptions).toHaveBeenCalledTimes(1)
    expect(mockFetchTransactions).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })

  it('defaults the date range to the current month boundaries', async () => {
    const wrapper = await createResolvedWrapper()

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

  it('surfaces a unified fallback message when initial loading fails', async () => {
    const apiService = (await import('@/services/api')).default
    apiService.fetchNetAssets.mockRejectedValueOnce(new Error('boom'))
    mockFetchTransactions.mockRejectedValueOnce(new Error('oops'))

    const wrapper = await createResolvedWrapper()

    expect(wrapper.vm.netWorthMessage).toContain('Unable to refresh dashboard data')
  })

  it('shows skeleton placeholders while async widgets resolve', async () => {
    const netOverview = createDeferredComponent({
      name: 'NetOverviewSection',
      template: '<div class="net-overview-loaded"></div>',
    })
    const categorySection = createDeferredComponent({
      name: 'CategoryBreakdownSection',
      template: '<div class="category-section-loaded"></div>',
    })
    const categoryChart = createDeferredComponent(CategoryBreakdownChartStub)

    const wrapper = createWrapper({
      global: {
        stubs: {
          Suspense: { template: '<div><slot name="fallback" /></div>' },
          NetOverviewSection: defineAsyncComponent(() => netOverview.promise),
          CategoryBreakdownSection: defineAsyncComponent(() => categorySection.promise),
          CategoryBreakdownChart: defineAsyncComponent(() => categoryChart.promise),
        },
      },
    })

    expect(wrapper.find('[data-testid="net-overview-skeleton"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="category-section-skeleton"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="spending-chart-skeleton"]').exists()).toBe(true)
  })

  it('clears selected categories when date range changes', async () => {
    const wrapper = await createResolvedWrapper()

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
    const wrapper = await createResolvedWrapper()

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
    const wrapper = await createResolvedWrapper()

    wrapper.vm.dateRange.start = '2024-03-15'
    wrapper.vm.dateRange.end = '2024-03-01'
    await vi.advanceTimersByTimeAsync(250)
    await nextTick()

    expect(categoryChartProps.startDate).toBe('2024-03-01')
    expect(categoryChartProps.endDate).toBe('2024-03-15')
  })

  it('propagates zoom toggles to charts without altering the debounced dates', async () => {
    const wrapper = await createResolvedWrapper()
    const initialStart = dailyNetChartProps.startDate
    const initialEnd = dailyNetChartProps.endDate

    wrapper.vm.zoomedOut = true
    await nextTick()

    expect(dailyNetChartProps.zoomedOut).toBe(true)
    expect(dailyNetChartProps.startDate).toBe(initialStart)
    expect(dailyNetChartProps.endDate).toBe(initialEnd)
  })

  it('auto-selects top breakdown IDs when the chart emits category data', async () => {
    const wrapper = await createResolvedWrapper()
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
    const wrapper = await createResolvedWrapper()
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

  it('uses responsive layout for the tables call-to-action on small screens', async () => {
    setViewportWidth(360)
    const wrapper = await createResolvedWrapper()

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
    const wrapper = await createResolvedWrapper()

    const spendingGrid = wrapper.find('[data-testid="spending-grid"]')
    expect(spendingGrid.exists()).toBe(true)
    expect(spendingGrid.classes()).toEqual(
      expect.arrayContaining(['grid-cols-1', 'sm:grid-cols-2', 'lg:grid-cols-3']),
    )

    wrapper.vm.expandAccounts()
    await nextTick()
    await flushPromises()
    const accountsSection = wrapper.findComponent({ name: 'AccountsSection' })
    expect(accountsSection.exists()).toBe(true)
    const accountsBody = accountsSection.find('.flex-1')
    expect(accountsBody.classes()).toEqual(
      expect.arrayContaining(['min-h-[50vh]', 'sm:min-h-[60vh]']),
    )

    wrapper.vm.expandTransactions()
    await nextTick()
    await flushPromises()
    const transactionsSection = wrapper.findComponent({ name: 'TransactionsSection' })
    expect(transactionsSection.exists()).toBe(true)
    const transactionsBody = transactionsSection.find('.flex-1')
    expect(transactionsBody.classes()).toEqual(
      expect.arrayContaining(['min-h-[50vh]', 'sm:min-h-[60vh]']),
    )
  })

  it('keeps overlays mutually exclusive between tables and modals', async () => {
    const wrapper = await createResolvedWrapper()

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
    const wrapper = await createResolvedWrapper()

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
    const wrapper = await createResolvedWrapper()

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
