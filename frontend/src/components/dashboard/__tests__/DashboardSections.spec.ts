// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount, RouterLinkStub } from '@vue/test-utils'
import NetOverviewSection from '../NetOverviewSection.vue'
import CategoryBreakdownSection from '../CategoryBreakdownSection.vue'
import AccountsSection from '../AccountsSection.vue'
import TransactionsSection from '../TransactionsSection.vue'
import InsightsRow from '../InsightsRow.vue'

const DateRangeSelectorStub = {
  name: 'DateRangeSelector',
  props: ['startDate', 'endDate', 'zoomedOut'],
  emits: ['update:start-date', 'update:end-date', 'update:zoomed-out'],
  template: '<div class="date-range-stub" @click="$emit(\'update:start-date\', startDate)"></div>',
}

const ChartDetailsSidebarStub = {
  name: 'ChartDetailsSidebar',
  props: ['granularity'],
  template: '<button class="chart-details-sidebar__toggle accent-toggle-btn">Overlays</button>',
}

const DailyNetChartStub = {
  name: 'DailyNetChart',
  props: {
    startDate: { type: String, required: true },
    endDate: { type: String, required: true },
    zoomedOut: { type: Boolean, default: false },
    basis: { type: String, default: 'economic' },
  },
  emits: ['summary-change', 'data-change', 'bar-click'],
  template:
    '<div class="daily-net-chart" @click="$emit(\'bar-click\', startDate)"><div class="daily-net-chart__title-shell"><slot name="title" granularity-title="Monthly" /></div><div class="daily-net-chart__controls-shell"><slot name="controls" granularity="monthly" /></div></div>',
}

const SafeToSpendCardStub = {
  name: 'SafeToSpendCard',
  props: ['payload', 'loading', 'error', 'selectedMode'],
  emits: ['update:mode'],
  template:
    '<button class="safe-spend-stub" @click="$emit(\'update:mode\', \'week\')">Safe Spend</button>',
}

const FinancialSummaryStub = {
  name: 'FinancialSummary',
  template: '<div class="financial-summary-stub" />',
  props: ['summary', 'chartData', 'zoomedOut', 'startDate', 'endDate'],
  emits: ['select-date'],
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
const BaseButtonStub = {
  name: 'BaseButton',
  template: '<button class="base-button-stub" @click="$emit(\'click\')"><slot /></button>',
}
const BasePanelStub = { name: 'BasePanel', template: '<div class="base-panel-stub"><slot /></div>' }

describe('Dashboard section components', () => {
  it('renders net overview content and forwards slot content', () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: {
        currentDate: 'January 1, 2025',
        activityStatusMessage: 'Largest expense was Rent.',
        dateRange: { start: '2025-01-01', end: '2025-01-31' },
        debouncedRange: { start: '2025-01-01', end: '2025-01-31' },
        zoomedOut: false,
        netSummary: { totalIncome: 10, totalExpenses: 1, totalNet: 9 },
        chartData: [],
        safeToSpend: { amount_cents: 4200, status: 'caution' },
        safeToSpendMode: 'today',
        periodTransactionCount: 12,
      },
      global: {
        stubs: {
          DateRangeSelector: DateRangeSelectorStub,
          ChartDetailsSidebar: ChartDetailsSidebarStub,
          TopAccountSnapshot: true,
          DailyNetChart: DailyNetChartStub,
          SafeToSpendCard: SafeToSpendCardStub,
          FinancialSummary: FinancialSummaryStub,
          RouterLink: RouterLinkStub,
        },
      },
      slots: {
        summary: '<div class="summary-slot">Custom Summary</div>',
      },
    })

    expect(wrapper.text()).toContain('Overview')
    expect(wrapper.text()).toContain('January 1, 2025')
    expect(wrapper.get('[data-testid="activity-status"]').text()).toContain(
      'Largest expense was Rent.',
    )
    expect(wrapper.text()).not.toContain('Welcome')
    expect(wrapper.find('.summary-slot').exists()).toBe(true)
    // Now tier: one raised lead plus an open supporting rail, not three equal cards.
    const tier = wrapper.get('[data-testid="now-tier"]')
    expect(tier.findAll('.surface-primary')).toHaveLength(1)
    expect(tier.findAll('.surface-normal')).toHaveLength(0)
    expect(tier.get('[data-testid="now-rail"]').text()).toContain('Economic net')
    expect(wrapper.findComponent(DateRangeSelectorStub).props()).toMatchObject({
      startDate: '2025-01-01',
      endDate: '2025-01-31',
      zoomedOut: false,
    })
    expect(wrapper.findComponent(DailyNetChartStub).props()).toMatchObject({
      startDate: '2025-01-01',
      endDate: '2025-01-31',
    })
    expect(wrapper.findComponent(SafeToSpendCardStub).props()).toMatchObject({
      payload: { amount_cents: 4200, status: 'caution' },
      selectedMode: 'today',
    })
    const transactionsCard = wrapper.get('[data-testid="transactions-card"]')
    expect(transactionsCard.text()).toContain('12 transactions in selected period')
    expect(transactionsCard.text()).not.toContain('to review')
    expect(transactionsCard.classes()).not.toContain('surface-attention')
    expect(wrapper.get('[data-testid="safe-to-spend-scope"]').text()).toContain(
      'not filtered by chart dates',
    )
    expect(wrapper.get('[data-testid="cash-direction-period"]').text()).toContain(
      'Jan 1 – Jan 31, 2025',
    )
    expect(wrapper.findAll('.net-overview-review-status')).toHaveLength(1)
    const html = wrapper.html()
    expect(html.indexOf('data-testid="now-tier"')).toBeLessThan(
      html.indexOf('data-testid="daily-net-timeframe-toggle"'),
    )

    const timeframeButtons = wrapper.findAll(
      '[data-testid="daily-net-timeframe-toggle"] .daily-net-timeframe-btn',
    )
    expect(timeframeButtons).toHaveLength(7)
    timeframeButtons.forEach((button) => {
      expect(button.classes()).toContain('accent-toggle-btn')
    })

    const overlayTrigger = wrapper.find('.chart-details-sidebar__toggle')
    expect(overlayTrigger.exists()).toBe(true)
    expect(overlayTrigger.classes()).toContain('accent-toggle-btn')

    expect(wrapper.get('[data-testid="daily-net-timeframe-toggle"]').exists()).toBe(true)
  })

  it('opens the review workflow from the dashboard hero count', async () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: {
        dateRange: { start: '2025-01-01', end: '2025-01-31' },
        debouncedRange: { start: '2025-01-01', end: '2025-01-31' },
        netSummary: { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
        periodTransactionCount: 1,
      },
      global: {
        stubs: {
          DateRangeSelector: DateRangeSelectorStub,
          ChartDetailsSidebar: ChartDetailsSidebarStub,
          TopAccountSnapshot: true,
          DailyNetChart: DailyNetChartStub,
          SafeToSpendCard: SafeToSpendCardStub,
          FinancialSummary: FinancialSummaryStub,
          RouterLink: RouterLinkStub,
        },
      },
    })

    expect(wrapper.get('[data-testid="transactions-card"]').text()).toContain(
      '1 transaction in selected period',
    )
    await wrapper.get('.net-overview-review-status').trigger('click')

    expect(wrapper.emitted('open-review')).toHaveLength(1)
  })

  const sectionStubs = {
    DateRangeSelector: DateRangeSelectorStub,
    ChartDetailsSidebar: ChartDetailsSidebarStub,
    TopAccountSnapshot: true,
    DailyNetChart: DailyNetChartStub,
    SafeToSpendCard: SafeToSpendCardStub,
    FinancialSummary: FinancialSummaryStub,
    RouterLink: RouterLinkStub,
  }
  const baseSectionProps = {
    dateRange: { start: '2025-01-08', end: '2025-01-17' },
    debouncedRange: { start: '2025-01-08', end: '2025-01-17' },
    netSummary: { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
  }

  it('shows zero, loading and error transaction counts without urgency', () => {
    const zero = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, periodTransactionCount: 0 },
      global: { stubs: sectionStubs },
    })
    expect(zero.get('[data-testid="transactions-card"]').text()).toContain(
      'No transactions in this period',
    )

    const failed = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, periodTransactionCount: 0, periodTransactionCountError: true },
      global: { stubs: sectionStubs },
    })
    const failedText = failed.get('[data-testid="transactions-card"]').text()
    expect(failedText).toContain('Transaction count unavailable')
    expect(failedText).not.toContain('No transactions')
  })

  it('renders an actionable reconnect alert only when connections need reconnection', () => {
    const none = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, reconnectCount: 0 },
      global: { stubs: sectionStubs },
    })
    expect(none.find('[data-testid="reconnect-alert"]').exists()).toBe(false)

    const two = shallowMount(NetOverviewSection, {
      props: {
        ...baseSectionProps,
        reconnectCount: 2,
        loadErrorMessage: 'Unable to refresh dashboard data.',
      },
      global: { stubs: { ...sectionStubs, RouterLink: RouterLinkStub } },
    })
    const alert = two.get('[data-testid="reconnect-alert"]')
    expect(alert.text()).toContain('2 connections need reconnection')
    expect(alert.findComponent(RouterLinkStub).props('to')).toBe('/accounts')
    expect(two.get('[data-testid="load-error-notice"]').text()).toContain('Unable to refresh')
  })

  it('shows the same selected period beside the picker, cash direction and chart', () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: baseSectionProps,
      global: { stubs: sectionStubs },
    })
    expect(wrapper.findComponent(DateRangeSelectorStub).props()).toMatchObject({
      startDate: '2025-01-08',
      endDate: '2025-01-17',
    })
    expect(wrapper.findComponent(DailyNetChartStub).props()).toMatchObject({
      startDate: '2025-01-08',
      endDate: '2025-01-17',
    })
    expect(wrapper.findComponent(FinancialSummaryStub).props()).toMatchObject({
      startDate: '2025-01-08',
      endDate: '2025-01-17',
    })
    expect(wrapper.get('[data-testid="selected-period"]').text()).toContain('Jan 8 – Jan 17, 2025')
    expect(wrapper.get('[data-testid="cash-direction-period"]').text()).toContain(
      'Jan 8 – Jan 17, 2025',
    )
  })

  it('marks exactly one period control active and shows Custom for manual dates', () => {
    const preset = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, netTimeframe: 'rolling_30' },
      global: { stubs: sectionStubs },
    })
    const pressed = preset
      .findAll('.daily-net-timeframe-btn')
      .filter((button) => button.attributes('aria-pressed') === 'true')
    expect(pressed).toHaveLength(1)
    expect(pressed[0].text()).toBe('30D')
    expect(preset.find('[data-testid="daily-net-timeframe-custom"]').exists()).toBe(false)

    const custom = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, netTimeframe: 'custom' },
      global: { stubs: sectionStubs },
    })
    expect(
      custom
        .findAll('.daily-net-timeframe-btn')
        .some((b) => b.attributes('aria-pressed') === 'true'),
    ).toBe(false)
    expect(custom.get('[data-testid="daily-net-timeframe-custom"]').text()).toBe('Custom')
  })

  it('titles the chart with the bucket granularity and passes it to the overlay controls', async () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, netTimeframe: 'ytd' },
      global: { stubs: sectionStubs },
    })
    // Cash movement is the default measure; economic activity is an explicit choice.
    expect(wrapper.get('.daily-net-chart-title').text()).toContain('Cash Movement')
    expect(wrapper.findComponent(DailyNetChartStub).props('basis')).toBe('cash')
    await wrapper.get('[data-testid="net-basis-economic"]').trigger('click')
    expect(wrapper.findComponent(DailyNetChartStub).props('basis')).toBe('economic')
    expect(wrapper.get('.daily-net-chart-title').text()).toContain('Economic Net')
    expect(wrapper.get('[data-testid="net-granularity"]').text()).toBe('· Monthly')
    expect(wrapper.findComponent(ChartDetailsSidebarStub).props('granularity')).toBe('monthly')
    expect(wrapper.html()).not.toContain('comparison-mode')
  })

  it('discloses refund adjustments only when the period has refunds', async () => {
    const none = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, netSummary: { totalIncome: 1000, totalExpenses: -300, totalRefunds: 0, totalNet: 700 } },
      global: { stubs: sectionStubs },
    })
    await none.get('[data-testid="net-basis-economic"]').trigger('click')
    expect(none.get('[data-testid="net-chart-totals"]').text()).toBe('Income $1,000.00 · Expenses ($300.00)')

    const refunded = shallowMount(NetOverviewSection, {
      props: { ...baseSectionProps, netSummary: { totalIncome: 1000, totalExpenses: -300, totalRefunds: 25, totalNet: 725 } },
      global: { stubs: sectionStubs },
    })
    await refunded.get('[data-testid="net-basis-economic"]').trigger('click')
    const text = refunded.get('[data-testid="net-chart-totals"]').text()
    expect(text).toContain('Economic income $1,000.00')
    expect(text).toContain('Refunds $25.00')
    expect(text).toContain('Net $725.00, excluding transfers')
    expect(refunded.get('[data-testid="cash-direction-totals"]').text()).toBe(text)
  })

  it('forwards unusual-day selection from the financial summary', async () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: baseSectionProps,
      global: { stubs: sectionStubs },
    })
    wrapper.findComponent(FinancialSummaryStub).vm.$emit('select-date', '2025-01-10')
    expect(wrapper.emitted('select-date')?.[0]).toEqual(['2025-01-10'])
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
          BaseButton: BaseButtonStub,
          BasePanel: BasePanelStub,
        },
      },
      slots: {
        'after-total': '<span class="after-total">extra</span>',
      },
    })

    const buttons = wrapper.findAllComponents(BaseButtonStub)
    await buttons[0].vm.$emit('click')
    await buttons[1].vm.$emit('click')
    await buttons[2].vm.$emit('click')

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
      global: {
        stubs: {
          AccountsTable: AccountsTableStub,
          BaseButton: BaseButtonStub,
          BasePanel: BasePanelStub,
        },
      },
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
          BaseButton: BaseButtonStub,
          BasePanel: BasePanelStub,
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

  it('shows cash money out with its debt-payment inclusion on the first viewport', () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: {
        ...baseSectionProps,
        netSummary: {
          totalIncome: 1000,
          totalExpenses: -300,
          totalRefunds: 0,
          totalNet: 700,
          totalMoneyIn: 1000,
          totalMoneyOut: 900,
          totalNetCash: 100,
          cashBreakdown: { debt_payment_out: 600, investment_allocation_out: 0, unclassified_out: 75 },
        },
      },
      global: { stubs: sectionStubs },
    })
    expect(wrapper.get('[data-testid="cash-out-amount"]').text()).toBe('$900.00')
    const includes = wrapper.get('[data-testid="cash-out-includes"]').text()
    expect(includes).toContain('$600.00 card and loan payments')
    expect(includes).toContain('$75.00 needs classification')
    expect(wrapper.get('[data-testid="net-chart-totals"]').text()).toContain('Money out $900.00')
  })

  it('says unavailable instead of $0 when cash movement was not supplied', () => {
    const wrapper = shallowMount(NetOverviewSection, {
      props: baseSectionProps,
      global: { stubs: sectionStubs },
    })
    expect(wrapper.find('[data-testid="cash-out-amount"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="cash-out-unavailable"]').text()).toBe('Unavailable')
  })
})

