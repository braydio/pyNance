// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { vi } from 'vitest'
import { ref } from 'vue'
import Accounts from '../Accounts.vue'
import api from '@/services/api'
import { fetchAccountActivityBreakdown, fetchNetChanges, rangeToDates } from '@/api/accounts'
import { fetchTransactions } from '@/api/transactions'
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

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn(async () => ({
    transactions: [{ transaction_id: 't1', amount: -12, name: 'Coffee' }],
    total: 25,
  })),
}))

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: (...args) => useAccountHistoryMock(...args),
}))

vi.mock('@/api/accounts', () => ({
  fetchNetChanges: vi
    .fn()
    .mockResolvedValue({ status: 'success', data: { income: 0, expense: 0, net: 0 } }),
  fetchAccountActivityBreakdown: vi.fn(async () => ({
    status: 'success',
    accounts: [
      { account_id: 'acc-1', name: 'Checking', transaction_count: 3, transaction_value_abs: 130 },
      { account_id: 'acc-2', name: 'Savings', transaction_count: 2, transaction_value_abs: 750 },
    ],
  })),
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

  describe('actions sidebar', () => {
    const LayoutStub = {
      props: ['modelValue'],
      emits: ['update:modelValue'],
      template: `<div>
        <span data-testid="active">{{ modelValue }}</span>
        <button v-for="tab in ['Summary', 'Transactions', 'Charts', 'Connections']" :key="tab"
          :data-testid="'go-' + tab" @click="$emit('update:modelValue', tab)" />
        <aside v-if="$slots.sidebar" data-testid="tabbed-sidebar"><slot name="sidebar" /></aside>
      </div>`,
    }
    const mountPage = () =>
      shallowMount(Accounts, {
        global: {
          stubs: {
            TabbedPageLayout: LayoutStub,
            AccountActionsSidebar: true,
            LinkedAccountsSection: true,
          },
        },
      })

    it('does not reserve a sidebar gutter on the Overview tab', () => {
      const wrapper = mountPage()
      expect(wrapper.get('[data-testid="active"]').text()).toBe('Summary')
      expect(wrapper.find('[data-testid="tabbed-sidebar"]').exists()).toBe(false)
    })

    it.each(['Transactions', 'Connections'])(
      'shows the actions sidebar on the %s tab',
      async (tab) => {
        const wrapper = mountPage()
        await wrapper.get(`[data-testid="go-${tab}"]`).trigger('click')
        expect(
          wrapper.find('[data-testid="tabbed-sidebar"] account-actions-sidebar-stub').exists(),
        ).toBe(true)
      },
    )

    it('leaves Trends full width as well', async () => {
      const wrapper = mountPage()
      await wrapper.get('[data-testid="go-Charts"]').trigger('click')
      expect(wrapper.find('[data-testid="tabbed-sidebar"]').exists()).toBe(false)
    })
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
    expect(html.indexOf('account-status')).toBeLessThan(
      html.indexOf('Money movement in selected period'),
    )
    expect(html.indexOf('Money movement in selected period')).toBeLessThan(
      html.indexOf('Most Active Accounts'),
    )
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
        html.indexOf('Money movement in selected period'),
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

  describe('account drill-in and period integrity', () => {
    const stubs = {
      TabbedPageLayout: {
        template:
          '<div><slot name="header" /><slot name="Summary" /><slot name="Transactions" /></div>',
      },
      AccountActionsSidebar: true,
      LinkedAccountsSection: true,
      Card: { template: '<div><slot /></div>' },
      PageHeader: { template: '<div />' },
      UiButton: { inheritAttrs: true, template: '<button v-bind="$attrs"><slot /></button>' },
      SkeletonCard: true,
      RetryError: {
        props: ['message'],
        template:
          '<button data-testid="retry-error" @click="$emit(\'retry\')">{{ message }}</button>',
      },
      AccountBalanceHistoryChart: true,
      TransactionsTable: {
        props: ['transactions'],
        template: '<div data-testid="tx-table">{{ transactions.length }}</div>',
      },
      AccountPortfolioOverview: true,
      AccountPortfolioList: true,
      RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' },
    }
    const mountSummary = (accountList) => {
      api.getAccounts.mockResolvedValueOnce({ accounts: accountList })
      return shallowMount(Accounts, { global: { stubs } })
    }
    const card = {
      account_id: 'acc-1',
      name: 'Travel Card',
      type: 'credit',
      balance: -250,
      credit_limit: 1000,
      apr: 24.99,
      apr_source: 'provider',
      institution_name: 'Bank',
      mask: '4242',
      interest_paid_recent: { total: 12.5, window_days: 90 },
    }

    it('keeps the link actions in a compact panel on Overview instead of a sidebar', async () => {
      const wrapper = mountSummary([card])
      await flushPromises()
      const panel = wrapper.get('[data-testid="link-account-panel"]')
      expect(panel.text()).toContain('Link an account')
      expect(panel.find('account-actions-sidebar-stub').exists()).toBe(true)
      expect(wrapper.findAll('account-actions-sidebar-stub')).toHaveLength(1) // no duplicated actions
      expect(panel.element.hasAttribute('open')).toBe(false)
    })

    it('attaches the period to the analysis it controls and says it is not a global filter', async () => {
      const wrapper = mountSummary([card])
      await flushPromises()
      const header = wrapper.get('[data-testid="accounts-period-bar"]')
      expect(header.text()).toContain('Activity & history')
      expect(header.get('[data-testid="accounts-period-scope"]').text()).toContain(
        'does not change the balances above',
      )
      expect(header.find('[data-testid="history-range-select"]').exists()).toBe(true)
      // The portfolio overview and ledger come before the period control.
      const html = wrapper.html()
      expect(html.indexOf('portfolio-overview')).toBeLessThan(html.indexOf('accounts-period-bar'))
      expect(html.indexOf('portfolio-list')).toBeLessThan(html.indexOf('accounts-period-bar'))
    })

    it('uses one breakdown request for the selected period instead of per-account calls', async () => {
      const wrapper = mountSummary([card, { ...card, account_id: 'acc-2', name: 'Other' }])
      await flushPromises()
      expect(fetchAccountActivityBreakdown).toHaveBeenCalledTimes(1)
      expect(fetchAccountActivityBreakdown).toHaveBeenCalledWith({
        start_date: '2024-01-01',
        end_date: '2024-01-30',
      })
      expect(wrapper.text()).toContain('2024-01-01 – 2024-01-30')
    })

    it('requests the selected account list for the same period, not a fixed recent list', async () => {
      mountSummary([card])
      await flushPromises()
      expect(fetchTransactions).toHaveBeenCalledWith({
        account_ids: ['acc-1'],
        start_date: '2024-01-01',
        end_date: '2024-01-30',
        page: 1,
        page_size: 10,
      })
    })

    it('changing the period reloads movement, activity ranking and the account list together', async () => {
      const wrapper = mountSummary([card])
      await flushPromises()
      rangeToDates.mockReturnValue({ start: '2023-10-03', end: '2024-01-30' })
      fetchNetChanges.mockClear()
      fetchTransactions.mockClear()
      fetchAccountActivityBreakdown.mockClear()
      await wrapper.get('[data-testid="history-range-select"]').setValue('90d')
      await flushPromises()
      expect(fetchNetChanges).toHaveBeenCalledWith('acc-1', {
        start_date: '2023-10-03',
        end_date: '2024-01-30',
      })
      expect(fetchTransactions).toHaveBeenCalledWith(
        expect.objectContaining({ start_date: '2023-10-03' }),
      )
      expect(fetchAccountActivityBreakdown).toHaveBeenCalledWith({
        start_date: '2023-10-03',
        end_date: '2024-01-30',
      })
      rangeToDates.mockReturnValue({ start: '2024-01-01', end: '2024-01-30' })
    })

    it('labels money movement honestly and keeps balance change separate', async () => {
      fetchNetChanges.mockResolvedValue({
        status: 'success',
        data: {
          money_in: 500,
          money_out: 200,
          net_movement: 300,
          balance_change: 120,
          income: 500,
          expense: 200,
          net: 300,
        },
      })
      const wrapper = mountSummary([card])
      await flushPromises()
      const text = wrapper.text()
      expect(text).toContain('Money movement in selected period')
      expect(text).toContain('Money in')
      expect(text).toContain('Net movement')
      expect(text).not.toMatch(/Net Change Summary|Income|Expense/)
      expect(wrapper.get('[data-testid="balance-change"]').text()).toContain('$120.00')
    })

    it('shows card facts with sources and unknowns, plus a transactions link for the account', async () => {
      const wrapper = mountSummary([card])
      await flushPromises()
      const focus = wrapper.get('[data-testid="account-focus"]').text()
      expect(focus).toContain('Amount owed')
      expect(focus).toContain('$250.00')
      expect(focus).toContain('25%')
      expect(focus).toContain('Calculated from limit and balance, not issuer-reported')
      expect(focus).toContain('24.99%')
      expect(focus).toContain('Provider-reported')
      expect(focus).toContain('Interest charged')
      expect(focus).not.toContain('Minimum payment')
      expect(
        wrapper.get('[data-testid="view-account-transactions"]').attributes('data-to'),
      ).toContain('account_id')
      expect(wrapper.get('[data-testid="recent-transactions-caption"]').text()).toContain(
        'Showing 1 of 25',
      )
    })

    it('shows deposits current vs available, loans without utilization, and an investments link', async () => {
      const deposit = mountSummary([
        {
          account_id: 'acc-1',
          name: 'Chk',
          type: 'depository',
          balance: 900,
          available_balance: 850,
        },
      ])
      await flushPromises()
      const depositText = deposit.get('[data-testid="account-focus"]').text()
      expect(depositText).toContain('Current balance')
      expect(depositText).toContain('Available')
      expect(depositText).toContain('$850.00')
      expect(depositText).not.toContain('Utilization')

      const loan = mountSummary([
        {
          account_id: 'acc-1',
          name: 'Loan',
          type: 'loan',
          balance: -9000,
          interest_rate_breakdown: { loan_interest_rate: { percentage: 5.5 } },
        },
      ])
      await flushPromises()
      const loanText = loan.get('[data-testid="account-focus"]').text()
      expect(loanText).toContain('Interest rate')
      expect(loanText).toContain('5.5%')
      expect(loanText).not.toContain('Utilization')

      const inv = mountSummary([
        {
          account_id: 'acc-1',
          name: 'Brokerage',
          type: 'brokerage',
          is_investment: true,
          balance: 5000,
        },
      ])
      await flushPromises()
      expect(inv.get('[data-testid="account-focus"] a').attributes('data-to')).toContain(
        '/investments',
      )
    })

    it('fails sections independently', async () => {
      fetchNetChanges.mockRejectedValueOnce(new Error('summary down'))
      const wrapper = mountSummary([card])
      await flushPromises()
      expect(wrapper.text()).toContain('Failed to load summary')
      expect(wrapper.get('[data-testid="tx-table"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('1. ')
    })

    it('offers a retry when accounts fail to load', async () => {
      api.getAccounts.mockRejectedValueOnce(new Error('offline'))
      const wrapper = shallowMount(Accounts, { global: { stubs } })
      await flushPromises()
      const retry = wrapper.get('[data-testid="retry-error"]')
      expect(retry.text()).toContain('Failed to load accounts')
      api.getAccounts.mockResolvedValueOnce({ accounts: [card] })
      await retry.trigger('click')
      await flushPromises()
      expect(wrapper.find('[data-testid="account-focus"]').exists()).toBe(true)
    })

    it('ignores a stale response when the selection changes mid-flight', async () => {
      let resolveFirst
      fetchNetChanges.mockImplementationOnce(
        () => new Promise((resolve) => (resolveFirst = resolve)),
      )
      const wrapper = mountSummary([card, { ...card, account_id: 'acc-2', name: 'Other' }])
      await flushPromises()
      wrapper.vm.accountId = 'acc-2'
      fetchNetChanges.mockResolvedValueOnce({
        status: 'success',
        data: { money_in: 7, money_out: 1, net_movement: 6 },
      })
      await flushPromises()
      resolveFirst({ status: 'success', data: { money_in: 999, money_out: 0, net_movement: 999 } })
      await flushPromises()
      expect(wrapper.text()).toContain('$7.00')
      expect(wrapper.text()).not.toContain('$999.00')
    })
  })
})
