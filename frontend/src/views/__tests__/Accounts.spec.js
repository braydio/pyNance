// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { ref } from 'vue'
import Accounts from '../Accounts.vue'
import api from '@/services/api'
import { fetchNetChanges } from '@/api/accounts'
import AccountPortfolioOverview from '@/components/accounts/AccountPortfolioOverview.vue'
import AccountPortfolioList from '@/components/accounts/AccountPortfolioList.vue'

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

const mockRoute = vi.hoisted(() => ({ query: { accountId: 'acc-1' } }))

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: mockRoute.query }),
  useRouter: () => ({}),
}))

vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), info: vi.fn() }),
}))

vi.mock('@/services/api', () => ({
  default: {
    getAccounts: vi.fn().mockResolvedValue({
      accounts: [
        { account_id: 'acc-1', name: 'Checking', display_name: 'Primary Checking' },
        { account_id: 'acc-2', name: 'Savings', display_name: 'Rainy Day Savings' },
      ],
    }),
    refreshAccounts: vi.fn().mockResolvedValue({ status: 'success' }),
    generatePlaidUpdateLinkToken: vi.fn().mockResolvedValue({ link_token: 'update-link' }),
  },
}))

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: (...args) => useAccountHistoryMock(...args),
}))

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchRecentTransactions: vi.fn(async (accountId) => {
    if (accountId === 'acc-2') {
      return { transactions: [{ amount: 500 }, { amount: -250 }] }
    }
    return { transactions: [{ amount: 100 }, { amount: -20 }, { amount: 10 }] }
  }),
  rangeToDates: vi.fn().mockReturnValue({ start: '2024-01-01', end: '2024-01-30' }),
}))

describe('Accounts.vue', () => {
  beforeEach(() => {
    mockRoute.query = { accountId: 'acc-1' }
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

  it('defaults most-active ranking to transaction count and supports value toggle', async () => {
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: { template: '<div><slot name="Summary" /></div>' },
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
    expect(wrapper.text()).toContain('1. Primary Checking')

    const select = wrapper.find('select.input.w-full.sm\\:w-72')
    await select.setValue('value')
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('1. Rainy Day Savings')
  })

  it('shows one persisted reconnect action per Item and keeps it until server health clears', async () => {
    const unhealthyAccounts = [
      {
        account_id: 'acc-1',
        name: 'Checking',
        institution_name: 'Bank',
        connection_status: {
          provider: 'plaid',
          state: 'reauth_required',
          requires_reauth: true,
          connection_id: 17,
        },
      },
      {
        account_id: 'acc-2',
        name: 'Savings',
        institution_name: 'Bank',
        connection_status: {
          provider: 'plaid',
          state: 'reauth_required',
          requires_reauth: true,
          connection_id: 17,
        },
      },
    ]
    api.getAccounts
      .mockResolvedValueOnce({ accounts: unhealthyAccounts })
      .mockResolvedValueOnce({ accounts: unhealthyAccounts })
    const wrapper = shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            template:
              '<div><slot name="header" /><slot name="Summary" /><slot name="Connections" /></div>',
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: false,
          Card: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div><slot name="title" /><slot name="subtitle" /></div>' },
          UiButton: { inheritAttrs: true, template: '<button v-bind="$attrs"><slot /></button>' },
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
    expect(
      wrapper.findAll('button').filter((button) => button.text().includes('Reconnect with Plaid')),
    ).toHaveLength(1)

    let linkSuccess
    window.Plaid = {
      create: vi.fn((options) => {
        linkSuccess = options.onSuccess
        return { open: vi.fn() }
      }),
    }
    await wrapper
      .findAll('button')
      .find((button) => button.text().includes('Reconnect with Plaid'))
      .trigger('click')
    await flushPromises()
    await linkSuccess()
    await flushPromises()
    expect(api.refreshAccounts).toHaveBeenCalledWith({ account_ids: ['acc-1', 'acc-2'] })
    expect(
      wrapper.findAll('button').filter((button) => button.text().includes('Reconnect with Plaid')),
    ).toHaveLength(1)
  })

  describe('Item reconnect session lifecycle', () => {
    const child = (account_id, connection_id) => ({
      account_id,
      name: account_id,
      institution_name: 'Bank',
      connection_status: {
        provider: 'plaid',
        state: 'reauth_required',
        requires_reauth: true,
        connection_id,
      },
    })
    const reconnectButtons = (wrapper) =>
      wrapper.findAll('button').filter((b) => /Reconnect with Plaid|Reconnecting/.test(b.text()))
    async function mountConnections(list) {
      api.getAccounts.mockReset()
      api.getAccounts.mockResolvedValue({ accounts: list })
      api.refreshAccounts.mockClear()
      api.generatePlaidUpdateLinkToken.mockClear()
      const wrapper = shallowMount(Accounts, {
        global: {
          stubs: {
            TabbedPageLayout: {
              template:
                '<div><slot name="header" /><slot name="Summary" /><slot name="Connections" /></div>',
            },
            AccountActionsSidebar: true,
            LinkedAccountsSection: false,
            Card: { template: '<div><slot /></div>' },
            PageHeader: { template: '<div />' },
            UiButton: { inheritAttrs: true, template: '<button v-bind="$attrs"><slot /></button>' },
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
      return wrapper
    }
    let openLinks = []
    afterEach(async () => {
      // Close any Link left open so the app-wide single-session lock is released.
      openLinks.forEach((link) => link.handlers?.onExit(null))
      openLinks = []
      await flushPromises()
    })
    function fakeLink() {
      const link = { handlers: null, open: vi.fn() }
      openLinks.push(link)
      window.Plaid = {
        create: vi.fn((handlers) => {
          link.handlers = handlers
          return { open: link.open }
        }),
      }
      return link
    }

    it('offers one action for a three-account Item and refreshes all three after Link', async () => {
      const wrapper = await mountConnections([child('a', 1), child('b', 1), child('c', 1)])
      expect(reconnectButtons(wrapper)).toHaveLength(1)
      expect(wrapper.get('[data-testid="connection-account-count"]').text()).toContain('3 accounts')
      const link = fakeLink()
      await reconnectButtons(wrapper)[0].trigger('click')
      await flushPromises()
      await link.handlers.onSuccess()
      await flushPromises()
      expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledTimes(1)
      expect(api.refreshAccounts).toHaveBeenCalledWith({ account_ids: ['a', 'b', 'c'] })
      // Server still reports reauth, so the warning and a usable action remain.
      expect(reconnectButtons(wrapper)).toHaveLength(1)
      expect(reconnectButtons(wrapper)[0].text()).toContain('Reconnect with Plaid')
      expect(wrapper.text()).toContain('still reports')
    })

    it('shows separate actions for two Items at one institution', async () => {
      const wrapper = await mountConnections([child('a', 1), child('b', 2)])
      expect(reconnectButtons(wrapper)).toHaveLength(2)
    })

    it('keeps the button busy until Link exits and a double click opens one session', async () => {
      const wrapper = await mountConnections([child('a', 1)])
      const link = fakeLink()
      const button = reconnectButtons(wrapper)[0]
      await button.trigger('click')
      await button.trigger('click')
      await flushPromises()
      expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledTimes(1)
      expect(link.open).toHaveBeenCalledTimes(1)
      expect(reconnectButtons(wrapper)[0].text()).toContain('Reconnecting')
      expect(reconnectButtons(wrapper)[0].attributes('disabled')).toBeDefined()
    })

    it('restores the action on cancel without marking the Item healthy', async () => {
      const wrapper = await mountConnections([child('a', 1)])
      const link = fakeLink()
      await reconnectButtons(wrapper)[0].trigger('click')
      await flushPromises()
      link.handlers.onExit(null)
      await flushPromises()
      const button = reconnectButtons(wrapper)[0]
      expect(button.text()).toContain('Reconnect with Plaid')
      expect(button.attributes('disabled')).toBeUndefined()
      expect(api.refreshAccounts).not.toHaveBeenCalled()
      expect(wrapper.text()).toContain('needs to be reconnected')
    })

    it('shows a failed verification and leaves the action usable', async () => {
      const wrapper = await mountConnections([child('a', 1)])
      const link = fakeLink()
      api.refreshAccounts.mockRejectedValueOnce(new Error('Refresh unavailable'))
      await reconnectButtons(wrapper)[0].trigger('click')
      await flushPromises()
      await link.handlers.onSuccess()
      await flushPromises()
      expect(wrapper.text()).toContain('Refresh unavailable')
      expect(reconnectButtons(wrapper)[0].text()).toContain('Reconnect with Plaid')
    })

    it('clears the warning only after the server reports the Item healthy', async () => {
      const wrapper = await mountConnections([child('a', 1)])
      const link = fakeLink()
      await reconnectButtons(wrapper)[0].trigger('click')
      await flushPromises()
      api.getAccounts.mockResolvedValue({
        accounts: [
          {
            ...child('a', 1),
            connection_status: { provider: 'plaid', state: 'healthy', connection_id: 1 },
          },
        ],
      })
      await link.handlers.onSuccess()
      await flushPromises()
      expect(reconnectButtons(wrapper)).toHaveLength(0)
    })
  })

  function mountWith(accountsResponse, slots = '<slot name="header" /><slot name="Summary" />') {
    api.getAccounts.mockResolvedValueOnce({ accounts: accountsResponse })
    return shallowMount(Accounts, {
      global: {
        stubs: {
          TabbedPageLayout: {
            props: ['tabs'],
            template: `<div><b v-for="t in tabs" :key="t.slot" class="tab-label">{{ t.label }}</b>${slots}</div>`,
          },
          AccountActionsSidebar: true,
          LinkedAccountsSection: true,
          Card: { template: '<div><slot /></div>' },
          PageHeader: { template: '<div />' },
          UiButton: { inheritAttrs: true, template: '<button v-bind="$attrs"><slot /></button>' },
          SkeletonCard: true,
          RetryError: true,
          AccountBalanceHistoryChart: true,
        },
      },
    })
  }

  it('shows selected-account state and net change before cross-account ranking', async () => {
    const wrapper = mountWith([
      {
        account_id: 'acc-1',
        name: 'Primary Checking',
        institution_name: 'Bank',
        mask: '1234',
        current_balance: 250,
      },
    ])
    await flushPromises()

    const status = wrapper.get('[data-testid="account-status"]')
    expect(status.text()).toContain('Primary Checking')
    expect(status.text()).toContain('•••• 1234')
    expect(status.text()).toContain('Connected')
    const html = wrapper.html()
    expect(html.indexOf('account-status')).toBeLessThan(html.indexOf('Net Change Summary'))
    expect(html.indexOf('Net Change Summary')).toBeLessThan(html.indexOf('Most Active Accounts'))
    expect(wrapper.findAll('[data-testid="accounts-refresh"]')).toHaveLength(1)
  })

  it('shows the connection-attention action only when a reconnect is needed', async () => {
    const healthy = mountWith([{ account_id: 'a', name: 'A' }])
    await flushPromises()
    expect(healthy.find('[data-testid="connection-attention"]').exists()).toBe(false)

    const unhealthy = mountWith([
      {
        account_id: 'a',
        name: 'A',
        connection_status: { provider: 'plaid', requires_reauth: true, connection_id: 3 },
      },
    ])
    await flushPromises()
    const banner = unhealthy.get('[data-testid="connection-attention"]')
    expect(banner.text()).toContain('needs to be reconnected')
    expect(banner.text()).not.toContain('Reconnect with Plaid')
  })

  it('exposes four task-oriented tabs in order', async () => {
    const wrapper = mountWith([{ account_id: 'a', name: 'A' }])
    await flushPromises()
    const labels = wrapper.findAll('.tab-label').map((node) => node.text())
    expect(labels).toEqual(['Overview', 'Activity', 'Trends', 'Connections'])
  })

  describe('portfolio overview', () => {
    const portfolioAccounts = [
      {
        account_id: 'chk',
        name: 'Checking',
        type: 'depository',
        balance: 1000,
        institution_name: 'Bank A',
      },
      {
        account_id: 'cc',
        name: 'Card',
        type: 'credit',
        balance: -250,
        credit_limit: 1000,
        institution_name: 'Bank B',
      },
    ]

    it('renders the all-accounts overview and ledger before account details and does not auto-select', async () => {
      mockRoute.query = {}
      fetchNetChanges.mockClear()
      const wrapper = mountWith(portfolioAccounts)
      await flushPromises()

      expect(wrapper.findComponent(AccountPortfolioOverview).exists()).toBe(true)
      expect(wrapper.findComponent(AccountPortfolioList).exists()).toBe(true)
      expect(wrapper.find('[data-testid="account-details-header"]').exists()).toBe(false)
      expect(fetchNetChanges).not.toHaveBeenCalled()
      expect(wrapper.get('#accounts-selector').element.value).toBe('')
      const html = wrapper.html()
      expect(html.indexOf('account-portfolio-overview')).toBeLessThan(
        html.indexOf('account-portfolio-list'),
      )
      expect(html.indexOf('account-portfolio-list')).toBeLessThan(
        html.indexOf('Most Active Accounts'),
      )
    })

    it('keeps the portfolio first when an account is selected and supports deep links', async () => {
      mockRoute.query = { accountId: 'cc' }
      const wrapper = mountWith(portfolioAccounts)
      await flushPromises()

      const html = wrapper.html()
      expect(html.indexOf('account-portfolio-list')).toBeLessThan(
        html.indexOf('account-details-header'),
      )
      expect(html.indexOf('account-details-header')).toBeLessThan(
        html.indexOf('Net Change Summary'),
      )
      expect(fetchNetChanges).toHaveBeenCalledWith('cc', expect.any(Object))
    })

    it('selecting from the ledger sets the account and back returns to all accounts', async () => {
      mockRoute.query = {}
      const wrapper = mountWith(portfolioAccounts)
      await flushPromises()

      wrapper.findComponent(AccountPortfolioList).vm.$emit('select', 'cc')
      await flushPromises()
      expect(wrapper.get('#accounts-selector').element.value).toBe('cc')
      expect(wrapper.find('[data-testid="account-details-header"]').exists()).toBe(true)

      await wrapper.get('[data-testid="account-details-header"] button').trigger('click')
      expect(wrapper.get('#accounts-selector').element.value).toBe('')
      expect(wrapper.find('[data-testid="account-details-header"]').exists()).toBe(false)
    })

    it('type chips toggle the shared filter and reset restores defaults', async () => {
      mockRoute.query = {}
      const wrapper = mountWith(portfolioAccounts)
      await flushPromises()

      wrapper.findComponent(AccountPortfolioOverview).vm.$emit('update:group', 'credit')
      await flushPromises()
      expect(wrapper.findComponent(AccountPortfolioList).props('filters').group).toBe('credit')
      wrapper.findComponent(AccountPortfolioOverview).vm.$emit('update:group', 'credit')
      await flushPromises()
      expect(wrapper.findComponent(AccountPortfolioList).props('filters').group).toBe('all')

      wrapper.findComponent(AccountPortfolioList).vm.$emit('update:filters', {
        ...wrapper.findComponent(AccountPortfolioList).props('filters'),
        query: 'card',
      })
      await flushPromises()
      wrapper.findComponent(AccountPortfolioList).vm.$emit('reset')
      await flushPromises()
      expect(wrapper.findComponent(AccountPortfolioList).props('filters').query).toBe('')
    })
  })
})
