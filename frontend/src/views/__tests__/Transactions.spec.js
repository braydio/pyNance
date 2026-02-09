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

describe('Transactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useRouteMock.mockReturnValue({ query: {} })
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
          PageHeader: {
            props: ['icon'],
            template: '<header><slot name="title" /><slot name="subtitle" /></header>',
          },
          RecurringTransactionSection: true,
          TabbedPageLayout: {
            template:
              '<div><slot name="header" /><slot /><slot name="Activity" /><slot name="Recurring" /><slot name="Scanner" /></div>',
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

    expect(text).toContain('Transactions')
    expect(text).toContain('3')
    expect(text).toContain('$19.00')
    expect(text).toContain('Unique categories')
    expect(text).toContain('2')
    expect(text).toContain('Unique merchants')
    expect(text).toContain('Unique accounts')
    expect(text).toContain('Unique institutions')
  })

  it('hides summary metrics when no filter is active', async () => {
    const { wrapper } = mountView({
      filtered: [{ transaction_id: 'tx-1', amount: 12 }],
    })

    await flushPromises()

    expect(wrapper.find('[data-testid="filter-summary"]').exists()).toBe(false)
  })
})
