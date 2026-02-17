import Accounts from '../Accounts.vue'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

function buildDateRanges() {
  const today = new Date()
  const end = today.toISOString().slice(0, 10)

  const start30 = new Date(today)
  start30.setDate(start30.getDate() - 30)

  const start90 = new Date(today)
  start90.setDate(start90.getDate() - 90)

  return {
    end,
    start30: start30.toISOString().slice(0, 10),
    start90: start90.toISOString().slice(0, 10),
  }
}

function stubAccountData(accountId) {
  const { end, start30, start90 } = buildDateRanges()

  cy.intercept('GET', `/api/accounts/${accountId}/net_changes*`, {
    statusCode: 200,
    body: { status: 'success', data: { income: 1000, expense: -400, net: 600 } },
  }).as(`net-${accountId}`)

  cy.intercept('GET', `/api/accounts/${accountId}/history?start_date=${start30}&end_date=${end}`, {
    statusCode: 200,
    body: {
      accountId,
      asOfDate: end,
      balances: [
        { date: end, balance: 50 },
        { date: end, balance: 75 },
      ],
    },
  }).as(`hist30-${accountId}`)

  cy.intercept('GET', `/api/accounts/${accountId}/history?start_date=${start90}&end_date=${end}`, {
    statusCode: 200,
    body: { accountId, asOfDate: end, balances: [] },
  }).as(`hist90-${accountId}`)

  cy.intercept('GET', `/api/transactions/${accountId}/transactions*`, {
    statusCode: 200,
    body: {
      status: 'success',
      data: {
        transactions: [
          { transaction_id: `${accountId}-t1`, amount: -20, description: `Coffee ${accountId}` },
        ],
      },
    },
  }).as(`tx-${accountId}`)
}

function mountPage({ accounts, initialQueryAccountId = null, clearStorage = true } = {}) {
  if (clearStorage) {
    localStorage.clear()
  }

  const accountList = accounts ?? [
    { account_id: 'acc1', name: 'Checking', mask: '1111' },
    { account_id: 'acc2', name: 'Savings', mask: '2222' },
  ]

  cy.intercept('GET', '/api/accounts/get_accounts*', {
    statusCode: 200,
    body: { accounts: accountList },
  }).as('accounts')

  accountList.forEach((account) => stubAccountData(account.account_id))

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/accounts', component: Accounts }],
  })

  const query = initialQueryAccountId ? `?accountId=${initialQueryAccountId}` : ''
  router.push(`/accounts${query}`)

  cy.mount(Accounts, {
    global: {
      plugins: [router, createPinia()],
      stubs: {
        AccountActionsSidebar: true,
        NetYearComparisonChart: true,
        AssetsBarTrended: true,
        AccountsReorderChart: true,
        AccountsTable: true,
        InstitutionTable: true,
      },
    },
  })

  return cy.wrap(router.isReady()).then(() => cy.wait('@accounts'))
}

describe('Accounts summary', () => {
  it('shows empty state when no accounts are available', () => {
    mountPage({ accounts: [] })

    cy.get('[data-testid="accounts-summary-empty"]').should('contain', 'No accounts linked')
    cy.get('[data-testid="account-context-selector"]').should('be.disabled')
    cy.get('[data-testid="tabbed-nav"]').contains('Transactions').should('be.disabled')
    cy.get('[data-testid="tabbed-nav"]').contains('Charts').should('be.disabled')
  })

  it('switches account context and syncs route query', () => {
    mountPage({ initialQueryAccountId: 'acc1' })

    cy.wait('@net-acc1')
    cy.wait('@tx-acc1')
    cy.wait('@hist30-acc1')

    cy.get('[data-testid="account-context-selector"]').select('acc2')

    cy.wait('@net-acc2')
    cy.wait('@tx-acc2')
    cy.wait('@hist30-acc2')
    cy.location('search').should('include', 'accountId=acc2')
    cy.contains('Coffee acc2')
  })

  it('persists selected range per account while switching', () => {
    mountPage({ initialQueryAccountId: 'acc1' })

    cy.wait('@hist30-acc1')
    cy.get('[data-testid="history-range-select"]').select('90d')
    cy.wait('@hist90-acc1')

    cy.get('[data-testid="account-context-selector"]').select('acc2')
    cy.wait('@hist30-acc2')
    cy.get('[data-testid="history-range-select"]').should('have.value', '30d')

    cy.get('[data-testid="account-context-selector"]').select('acc1')
    cy.wait('@hist90-acc1')
    cy.get('[data-testid="history-range-select"]').should('have.value', '90d')
  })
})
