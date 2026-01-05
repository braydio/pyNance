// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import NetOverviewSection from '../NetOverviewSection.vue'
import CategoryBreakdownSection from '../CategoryBreakdownSection.vue'
import AccountsSection from '../AccountsSection.vue'
import TransactionsSection from '../TransactionsSection.vue'
import InsightsRow from '../InsightsRow.vue'

const DateRangeSelectorStub = {
  name: 'DateRangeSelector',
  props: ['startDate', 'endDate', 'zoomedOut'],
  emits: ['update:start-date', 'update:end-date', 'update:zoomed-out'],
  template:
    '<div class="date-range-stub" @click="$emit(\'update:start-date\', startDate)"></div>',
}

const ChartDetailsSidebarStub = { name: 'ChartDetailsSidebar', template: '<div />' }

const DailyNetChartStub = {
  name: 'DailyNetChart',
  props: {
    startDate: { type: String, required: true },
    endDate: { type: String, required: true },
    zoomedOut: { type: Boolean, default: false },
  },
  emits: ['summary-change', 'data-change', 'bar-click'],
  template: '<div class="daily-net-chart" @click="$emit(\'bar-click\', startDate)" />',
}

const FinancialSummaryStub = {
  name: 'FinancialSummary',
  template: '<div class="financial-summary-stub" />',
  props: ['summary', 'chartData', 'zoomedOut', 'startDate', 'endDate'],
}

const ChartWidgetTopBarStub = {
  name: 'ChartWidgetTopBar',
  template: '<div><slot name="controls" /></div>',
}
const GroupedCategoryDropdownStub = {
  name: 'GroupedCategoryDropdown',
  props: ['groups', 'modelValue'],
  emits: ['update:modelValue'],
  template:
    '<div class="grouped-dropdown" @click="$emit(\'update:modelValue\', groups.map(g => g.id))"></div>',
}

const CategoryBreakdownChartStub = {
  name: 'CategoryBreakdownChart',
  props: ['startDate', 'endDate', 'selectedCategoryIds', 'groupOthers', 'breakdownType'],
  emits: ['summary-change', 'categories-change', 'bar-click'],
  template: '<div class="category-chart" @click="$emit(\'bar-click\', breakdownType)" />',
}

const AccountsTableStub = { name: 'AccountsTable', template: '<div class="accounts-table-stub" />' }
const TransactionsTableStub = {
  name: 'TransactionsTable',
  props: ['transactions', 'sortKey', 'sortOrder', 'search', 'currentPage', 'totalPages'],
  emits: ['sort', 'change-page'],
  template: '<div class="transactions-table-stub" @click="$emit(\'sort\', \'amount\')" />',
}
const PaginationControlsStub = {
  name: 'PaginationControls',
  props: ['currentPage', 'totalPages', 'pageSize', 'totalItems'],
  emits: ['change-page'],
  template: '<div class="pagination-stub" @click="$emit(\'change-page\', 2)" />',
}
const SpendingInsightsStub = { name: 'SpendingInsights', template: '<div class="insights-stub" />' }

describe('Dashboard section components', () => {
  it('renders net overview content and forwards slot content', () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: {
        userName: 'Casey',
        currentDate: 'January 1, 2025',
        netWorthMessage: 'In the black',
        dateRange: { start: '2025-01-01', end: '2025-01-31' },
        debouncedRange: { start: '2025-01-01', end: '2025-01-31' },
        zoomedOut: false,
        netSummary: { totalIncome: 10, totalExpenses: 1, totalNet: 9 },
        chartData: [],
      },
      global: {
        stubs: {
          DateRangeSelector: DateRangeSelectorStub,
          ChartDetailsSidebar: ChartDetailsSidebarStub,
          TopAccountSnapshot: true,
          DailyNetChart: DailyNetChartStub,
          FinancialSummary: FinancialSummaryStub,
        },
      },
      slots: {
        summary: '<div class="summary-slot">Custom Summary</div>',
      },
    })

    expect(wrapper.text()).toContain('Casey')
    expect(wrapper.text()).toContain('In the black')
    expect(wrapper.find('.summary-slot').exists()).toBe(true)
    expect(wrapper.findComponent(DateRangeSelectorStub).props()).toMatchObject({
      startDate: '2025-01-01',
      endDate: '2025-01-31',
      zoomedOut: false,
    })
    expect(wrapper.findComponent(DailyNetChartStub).props()).toMatchObject({
      startDate: '2025-01-01',
      endDate: '2025-01-31',
    })
  })

  it('renders category breakdown controls and emits change events', async () => {
    const wrapper = shallowMount(CategoryBreakdownSection, {
      props: {
        startDate: '2025-02-01',
        endDate: '2025-02-28',
        categoryGroups: [{ id: 'groceries', label: 'Groceries' }],
        selectedCategoryIds: ['groceries'],
        groupOthers: true,
        breakdownType: 'category',
        summary: { total: 150 },
      },
      global: {
        stubs: {
          ChartWidgetTopBar: ChartWidgetTopBarStub,
          GroupedCategoryDropdown: GroupedCategoryDropdownStub,
          CategoryBreakdownChart: CategoryBreakdownChartStub,
        },
      },
      slots: {
        'after-total': '<span class="after-total">extra</span>',
      },
    })

    const [categoryButton, merchantButton] = wrapper.findAll('button')
    await categoryButton.trigger('click')
    await merchantButton.trigger('click')
    await wrapper.find('button.btn').trigger('click')

    expect(wrapper.find('.after-total').exists()).toBe(true)
    expect(wrapper.emitted('change-breakdown')?.[0]).toEqual(['category'])
    expect(wrapper.emitted('change-breakdown')?.[1]).toEqual(['merchant'])
    expect(wrapper.emitted('toggle-group-others')).toBeTruthy()
    expect(wrapper.findComponent(CategoryBreakdownChartStub).props()).toMatchObject({
      startDate: '2025-02-01',
      endDate: '2025-02-28',
      selectedCategoryIds: ['groceries'],
    })
  })

  it('shows accounts section content and emits close', async () => {
    const wrapper = shallowMount(AccountsSection, {
      global: { stubs: { AccountsTable: AccountsTableStub } },
      slots: { default: '<div class="accounts-slot">Slot Content</div>' },
    })

    expect(wrapper.findComponent(AccountsTableStub).exists()).toBe(true)
    expect(wrapper.find('.accounts-slot').exists()).toBe(true)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('renders transactions section with pagination controls and forwards events', async () => {
    const wrapper = shallowMount(TransactionsSection, {
      props: {
        transactions: [{ id: 1 }],
        sortKey: 'amount',
        sortOrder: -1,
        search: 'rent',
        currentPage: 1,
        totalPages: 3,
        pageSize: 15,
        totalCount: 45,
      },
      global: {
        stubs: {
          TransactionsTable: TransactionsTableStub,
          PaginationControls: PaginationControlsStub,
        },
      },
      slots: { default: '<div class="transactions-slot">Extra</div>' },
    })

    expect(wrapper.findComponent(TransactionsTableStub).props()).toMatchObject({
      transactions: [{ id: 1 }],
      sortKey: 'amount',
      sortOrder: -1,
      search: 'rent',
      currentPage: 1,
      totalPages: 3,
    })
    await wrapper.findComponent(TransactionsTableStub).trigger('click')
    await wrapper.findComponent(PaginationControlsStub).trigger('click')
    await wrapper.find('button').trigger('click')

    expect(wrapper.emitted('sort')?.[0]).toEqual(['amount'])
    expect(wrapper.emitted('set-page')?.[0]).toEqual([2])
    expect(wrapper.emitted('close')).toBeTruthy()
    expect(wrapper.find('.transactions-slot').exists()).toBe(true)
  })

  it('positions children next to insights content', () => {
    const wrapper = shallowMount(InsightsRow, {
      global: { stubs: { SpendingInsights: SpendingInsightsStub } },
      slots: { default: '<div class="primary">Primary</div>' },
    })

    expect(wrapper.find('.primary').exists()).toBe(true)
    expect(wrapper.findComponent(SpendingInsightsStub).exists()).toBe(true)
  })
})
