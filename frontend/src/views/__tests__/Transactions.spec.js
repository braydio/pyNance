// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import Transactions from '../Transactions.vue'

const useTransactionsMock = vi.fn()

vi.mock('@/composables/useTransactions.js', () => ({
  useTransactions: (...args) => useTransactionsMock(...args),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
}))

describe('Transactions.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  function mountView({ isLoading = false, error = null } = {}) {
    const searchQuery = ref('')
    const currentPage = ref(1)
    const totalPages = ref(1)
    const totalCount = ref(0)
    const filteredTransactions = ref([])
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
          PageHeader: true,
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
})
