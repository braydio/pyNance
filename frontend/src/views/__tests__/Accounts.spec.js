// @vitest-environment jsdom
import { describe, it, expect, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import Accounts from '../Accounts.vue'
import { fetchNetChanges } from '@/api/accounts'

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

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchAccountHistory: vi.fn().mockResolvedValue({ balances: [] }),
  fetchRecentTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
  rangeToDates: vi.fn().mockReturnValue({ start: '2024-01-01', end: '2024-01-30' }),
}))

describe('Accounts.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
})
