// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import Transactions from '../Transactions.vue'

const useTransactionsMock = vi.fn()
const useRouteMock = vi.fn(() => ({ query: {} }))

vi.mock('@/composables/useTransactions.js', () => ({
  useTransactions: (...args) => useTransactionsMock(...args),
}))

vi.mock('vue-router', () => ({
  useRoute: () => useRouteMock(),
}))

const insightsFixture = {
  matching_count: 2005,
  gross_spend: 540,
  refunds: 40,
  net_spend: 500,
  income: 3000,
  inflow: {
    economic_income: 3000,
    all_credit_movements: 3300,
    transfers_in: 200,
    unclassified_in: 100,
  },
  uncategorized_count: 4,
  review_items: [
    {
      id: 'missing_category:t1',
      kind: 'missing_category',
      priority: 3,
      count: 4,
      amount_total: 80,
      transaction_ids: ['t1'],
      explanation: '4 transactions have no category.',
      evidence: ['Category is empty'],
      filter: { uncategorized: true },
    },
    {
      id: 'transfer_candidate:t2',
      kind: 'transfer_candidate',
      priority: 1,
      count: 1,
      amount_total: 100,
      transaction_ids: ['t2'],
      explanation: '1 transfer-looking transaction is not matched.',
      evidence: ['Provider labels it a transfer'],
      filter: { review: 'transfer_candidate' },
    },
  ],
  recurring_candidate_count: 2,
  transfer_pair_count: 1,
  coverage: { unclassified_count: 1 },
}
const apiMock = vi.hoisted(() => ({ getTransactionInsights: vi.fn(), getAccounts: vi.fn() }))
vi.mock('@/services/api', () => ({ default: apiMock }))

describe('Transactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useRouteMock.mockReturnValue({ query: {} })
    apiMock.getTransactionInsights.mockResolvedValue({ status: 'success', data: insightsFixture })
    apiMock.getAccounts.mockResolvedValue({ accounts: [] })
  })

  function mountView({ isLoading = false, error = null, query = {}, filtered = [] } = {}) {
    useRouteMock.mockReturnValue({ query })

    const searchQuery = ref('')
    const currentPage = ref(1)
    const totalPages = ref(1)
    const totalCount = ref(filtered.length)
    const filteredTransactions = ref(filtered)
    const paginatedTransactions = ref(filtered)
    const sortKey = ref(null)
    const sortOrder = ref(1)
    const isLoadingRef = ref(isLoading)
    const errorRef = ref(error)
    const changePage = vi.fn()
    const setPage = vi.fn()
    const setSort = vi.fn()
    const fetchTransactions = vi.fn()

    useTransactionsMock.mockReturnValue({
      searchQuery,
      currentPage,
      totalPages,
      totalCount,
      filteredTransactions,
      paginatedTransactions,
      changePage,
      setPage,
      sortKey,
      sortOrder,
      setSort,
      isLoading: isLoadingRef,
      error: errorRef,
      fetchTransactions,
    })

    const wrapper = shallowMount(Transactions, {
      global: {
        stubs: {
          AccountFilter: true,
          Card: { template: '<div><slot /></div>' },
          DateRangeSelector: true,
          ImportFileSelector: true,
          InternalTransferScanner: true,
          TransactionInsightsPanel: false,
          PageHeader: {
            props: ['icon'],
            template: '<header><slot name="title" /><slot name="subtitle" /></header>',
          },
          RecurringTransactionSection: true,
          TabbedPageLayout: {
            template:
              '<div><slot name="header" /><slot name="Activity" /><slot name="Recurring" /><slot name="Scanner" /></div>',
          },
          TypeSelector: true,
          UiButton: {
            template: '<button><slot /></button>',
          },
          UpdateTransactionsTable: true,
          SkeletonCard: { template: '<div data-testid="skeleton-card" />' },
          RetryError: {
            props: ['message'],
            emits: ['retry'],
            template:
              '<div data-testid="retry-error"><button data-testid="retry-button" @click="$emit(\'retry\')">Retry</button></div>',
          },
          PaginationControls: true,
        },
      },
    })

    return {
      wrapper,
      fetchTransactions,
      searchQuery,
      totalCount,
      sortKey,
    }
  }

  it('shows a skeleton card while transactions load', async () => {
    const { wrapper } = mountView({ isLoading: true })

    await flushPromises()

    expect(wrapper.find('[data-testid="skeleton-card"]').exists()).toBe(true)
  })

  it('renders retry state and triggers refetch when retry is clicked', async () => {
    const { wrapper, fetchTransactions } = mountView({ error: new Error('Network error') })

    await flushPromises()

    const retryButton = wrapper.find('[data-testid="retry-button"]')
    expect(retryButton.exists()).toBe(true)

    await retryButton.trigger('click')

    expect(fetchTransactions).toHaveBeenCalled()
  })

  it('shows summary metrics when a filter is active', async () => {
    const filtered = [
      {
        transaction_id: 'tx-1',
        amount: '-10.5',
        category: 'Food',
        merchant_name: 'Grocer',
        account_name: 'Checking',
        institution_name: 'Bank A',
      },
      {
        transaction_id: 'tx-2',
        amount: '25',
        category: 'Travel',
        merchant_name: 'Airline',
        account_name: 'Checking',
        institution_name: 'Bank A',
      },
      {
        transaction_id: 'tx-3',
        amount: 4.5,
        category: 'Food',
        merchant_name: 'Grocer',
        account_name: 'Savings',
        institution_name: 'Bank B',
      },
    ]

    const { wrapper } = mountView({ query: { tx_type: 'debit' }, filtered })

    await flushPromises()

    const summary = wrapper.find('[data-testid="filter-summary"]')
    expect(summary.exists()).toBe(true)
    const text = summary.text()
    expect(text).toContain('This page, signed total $19.00')
    expect(text).toContain('Type: debit')
    expect(wrapper.get('[data-testid="result-count"]').text()).toContain('3 on this page')
    expect(wrapper.get('[data-testid="filters-toggle"]').text()).toContain('(1)')
    expect(text).not.toContain('Unique categories')
  })

  it('clears active filters from the inline summary', async () => {
    const { wrapper } = mountView({
      query: { tx_type: 'debit' },
      filtered: [{ transaction_id: 'tx-1', amount: 1 }],
    })
    await flushPromises()

    await wrapper.get('[data-testid="clear-filters"]').trigger('click')

    expect(wrapper.find('[data-testid="filter-summary"]').exists()).toBe(false)
  })

  it('renders the scanner only in the Scanner tab and the table without opening tools', async () => {
    const { wrapper } = mountView({ filtered: [{ transaction_id: 'tx-1', amount: 12 }] })
    await flushPromises()

    expect(wrapper.html().split('<internal-transfer-scanner-stub').length - 1).toBe(1)
    expect(wrapper.find('update-transactions-table-stub').exists()).toBe(true)
    expect(wrapper.find('#activity-import').exists()).toBe(false)
  })

  it('discloses filters and import with accessible toggles', async () => {
    const { wrapper } = mountView()
    await flushPromises()

    const filters = wrapper.get('[data-testid="filters-toggle"]')
    expect(filters.attributes('aria-expanded')).toBe('false')
    await filters.trigger('click')
    expect(filters.attributes('aria-expanded')).toBe('true')
    expect(wrapper.get('#activity-filters').classes()).toContain('is-open')

    await wrapper.get('[data-testid="import-toggle"]').trigger('click')
    expect(wrapper.find('#activity-import').exists()).toBe(true)
  })

  it('hides summary metrics when no filter is active', async () => {
    const { wrapper } = mountView({
      filtered: [{ transaction_id: 'tx-1', amount: 12 }],
    })

    await flushPromises()

    expect(wrapper.find('[data-testid="filter-summary"]').exists()).toBe(false)
  })

  it('offers a toolbar Clear that resets search and filters together', async () => {
    const { wrapper } = mountView({
      query: { tx_type: 'debit' },
      filtered: [{ transaction_id: 'tx-1', amount: 1 }],
    })
    await flushPromises()
    const clear = wrapper.get('[data-testid="clear-search-filters"]')
    await wrapper.get('#transactions-search').setValue('coffee')
    await clear.trigger('click')
    expect(wrapper.get('#transactions-search').element.value).toBe('')
    expect(wrapper.find('[data-testid="clear-search-filters"]').exists()).toBe(false)
  })

  it('shows the toolbar Clear only when something can be cleared', async () => {
    const { wrapper } = mountView()
    await flushPromises()
    expect(wrapper.find('[data-testid="clear-search-filters"]').exists()).toBe(false)
  })

  describe('insights and toolbar', () => {
    it('loads server-side insights for the selected period and account, with a scope label', async () => {
      const { wrapper } = mountView()
      await flushPromises()
      expect(apiMock.getTransactionInsights).toHaveBeenCalledWith({
        start_date: undefined,
        end_date: undefined,
        account_ids: undefined,
        refresh: undefined,
      })
      expect(wrapper.get('[data-testid="insights-panel"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Last 30 days (pick a period to change)')
      expect(wrapper.get('[data-testid="metric-spending"]').text()).toContain('$500.00')
    })

    it('uses the query dates for insights and labels them', async () => {
      const { wrapper } = mountView({ query: { start_date: '2026-10-01', end_date: '2026-10-31' } })
      await flushPromises()
      expect(apiMock.getTransactionInsights).toHaveBeenCalledWith(
        expect.objectContaining({ start_date: '2026-10-01', end_date: '2026-10-31' }),
      )
      expect(wrapper.get('[data-testid="insights-scope"]').text()).toBe('2026-10-01 – 2026-10-31')
      expect(wrapper.get('[data-testid="period-preset"]').element.value).toBe('custom')
    })

    it('never presents a page as the whole matching set', async () => {
      const rows = Array.from({ length: 10 }, (_, i) => ({ transaction_id: `t${i}`, amount: 1 }))
      const { wrapper, totalCount } = mountView({ filtered: rows })
      totalCount.value = 2005
      await flushPromises()
      expect(wrapper.get('[data-testid="result-count"]').text()).toContain(
        '10 on this page · 2,005 matching',
      )
      expect(wrapper.get('[data-testid="result-count"]').text()).not.toContain('shown')
    })

    it('passes the chosen sort to the server filters and switches the client sort off', async () => {
      const { wrapper, sortKey } = mountView()
      sortKey.value = 'date'
      await flushPromises()
      await wrapper.get('[data-testid="sort-select"]').setValue('spend_desc')
      await flushPromises()
      const filtersRef = useTransactionsMock.mock.calls[0][2]
      expect(filtersRef.value.sort).toBe('spend_desc')
      expect(sortKey.value).toBe(null)
      await wrapper.get('[data-testid="sort-select"]').setValue('date_desc')
      expect(filtersRef.value.sort).toBeUndefined()
      expect(sortKey.value).toBe('date')
      expect(wrapper.findAll('[data-testid="sort-select"] option').map((o) => o.text())).toEqual([
        'Newest',
        'Oldest',
        'Largest spend',
        'Amount',
        'Merchant',
        'Category',
      ])
    })

    it('applies a period preset to the date filters and the insights request', async () => {
      const { wrapper } = mountView()
      await flushPromises()
      await wrapper.get('[data-testid="period-preset"]').setValue('30d')
      const filtersRef = useTransactionsMock.mock.calls[0][2]
      expect(filtersRef.value.start_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(filtersRef.value.end_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      await new Promise((resolve) => setTimeout(resolve, 350))
      expect(apiMock.getTransactionInsights).toHaveBeenLastCalledWith(
        expect.objectContaining({ start_date: filtersRef.value.start_date }),
      )
    })

    it('review cards narrow the explorer or open Transfer Review without editing anything', async () => {
      const { wrapper, searchQuery } = mountView()
      await flushPromises()
      await wrapper.get('[data-testid="review-missing_category"] button').trigger('click')
      expect(searchQuery.value).toBe('Uncategorized')
      await wrapper.get('[data-testid="review-transfer_candidate"] button').trigger('click')
      expect(wrapper.vm.activeTab).toBe('Scanner')
    })

    it('explains a missing server owner instead of failing silently', async () => {
      apiMock.getTransactionInsights.mockRejectedValueOnce({
        response: { data: { code: 'owner_not_configured' } },
      })
      const { wrapper } = mountView()
      await flushPromises()
      expect(wrapper.get('[data-testid="insights-error"]').text()).toContain(
        'not set up on this server',
      )
    })
  })
})
