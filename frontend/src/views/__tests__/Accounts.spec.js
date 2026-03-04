// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { ref } from 'vue'
import Accounts from '../Accounts.vue'
import { fetchNetChanges } from '@/api/accounts'

const normalizedHistory = ref([
  { date: '2024-01-01', balance: 120 },
  { date: '2024-01-02', balance: 135.5 },
])
const loadHistoryMock = vi.fn().mockResolvedValue(normalizedHistory.value)
const useAccountHistoryMock = vi.fn(() => ({
  history: normalizedHistory,
  balances: normalizedHistory,
  loading: ref(false),
  error: ref(null),
  isReady: ref(true),
  loadHistory: loadHistoryMock,
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({}),
}))

vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), info: vi.fn() }),
}))

vi.mock('@/services/api', () => ({
  default: {
    getAccounts: vi.fn().mockResolvedValue({
      accounts: [{ account_id: 'acc-1', name: 'Checking', display_name: 'Primary Checking' }],
    }),
  },
}))

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: (...args) => useAccountHistoryMock(...args),
}))

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchRecentTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
  rangeToDates: vi.fn().mockReturnValue({ start: '2024-01-01', end: '2024-01-30' }),
}))

describe('Accounts.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    loadHistoryMock.mockResolvedValue(normalizedHistory.value)
    normalizedHistory.value = [
      { date: '2024-01-01', balance: 120 },
      { date: '2024-01-02', balance: 135.5 },
    ]
  })

  it('matches snapshot', () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: ['TabbedPageLayout', 'AccountActionsSidebar', 'LinkedAccountsSection'],
      },
    })
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('passes AccountActionsSidebar into the tab layout sidebar slot', () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template: '<div><slot name="sidebar" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
        },
      },
    })

    expect(wrapper.find('account-actions-sidebar-stub').exists()).toBe(true)
  })

  it('renders non-zero net summary values from the response data envelope', async () => {
    fetchNetChanges.mockResolvedValue({
      status: 'success',
      data: { income: 1250.55, expense: 300.1, net: 950.45 },
    })

    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template: '<div><slot name="Summary" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
          Card: {
            template: '<div><slot /></div>',
          },
          PageHeader: {
            template: '<div><slot name="title" /><slot name="subtitle" /></div>',
          },
          UiButton: {
            template: '<button><slot /></button>',
          },
          SkeletonCard: true,
          RetryError: true,
          AccountBalanceHistoryChart: true,
          TransactionsTable: true,
          NetYearComparisonChart: true,
          AssetsBarTrended: true,
          AccountsReorderChart: true,
        },
      },
    })

    await flushPromises()
    await wrapper.vm.$nextTick()

    const text = wrapper.text()
    expect(text).toContain('$1,250.55')
    expect(text).toContain('$300.10')
    expect(text).toContain('$950.45')
  })

  it('uses the shared account-history composable range contract for chart data loading', async () => {
    shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template: '<div><slot name="Summary" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
          Card: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div><slot name="title" /><slot name="subtitle" /></div>' },
          UiButton: { template: '<button><slot /></button>' },
          SkeletonCard: true,
          RetryError: true,
          AccountBalanceHistoryChart: true,
          TransactionsTable: true,
          NetYearComparisonChart: true,
          AssetsBarTrended: true,
          AccountsReorderChart: true,
        },
      },
    })

    await flushPromises()

    expect(useAccountHistoryMock).toHaveBeenCalled()
    const [, passedRangeRef] = useAccountHistoryMock.mock.calls[0]
    expect(passedRangeRef.value).toBe('30d')
    expect(loadHistoryMock).toHaveBeenCalledWith()
  })

  it('passes normalized composable history into the balance chart', async () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template: '<div><slot name="Summary" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
          Card: {
            template: '<div><slot /></div>',
          },
          PageHeader: {
            template: '<div><slot name="title" /><slot name="subtitle" /></div>',
          },
          UiButton: {
            template: '<button><slot /></button>',
          },
          SkeletonCard: true,
          RetryError: true,
          AccountBalanceHistoryChart: {
            name: 'AccountBalanceHistoryChart',
            template: '<div data-testid="history-chart-proxy" />',
            props: ['historyData'],
          },
          TransactionsTable: true,
          NetYearComparisonChart: true,
          AssetsBarTrended: true,
          AccountsReorderChart: true,
        },
      },
    })

    await flushPromises()

    const chart = wrapper.getComponent({ name: 'AccountBalanceHistoryChart' })
    expect(chart.props('historyData')).toEqual(normalizedHistory.value)
  })
})
