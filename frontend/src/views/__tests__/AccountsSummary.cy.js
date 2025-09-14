import Accounts from '../Accounts.vue'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

function mountPage(account = 'acc1', expected = '@hist30', clear = true) {
  if (clear) {
    localStorage.clear()
  }
  const today = new Date()
  const end = today.toISOString().slice(0, 10)

  const start30 = new Date(today)
  start30.setDate(start30.getDate() - 30)
  const start30Str = start30.toISOString().slice(0, 10)

  const start90 = new Date(today)
  start90.setDate(start90.getDate() - 90)
  const start90Str = start90.toISOString().slice(0, 10)

  cy.intercept('GET', `/api/accounts/${account}/net_changes*`, {
    statusCode: 200,
    body: { status: 'success', data: { income: 1000, expense: -400, net: 600 } },
  }).as('net')

  cy.intercept('GET', `/api/accounts/${account}/history?start_date=${start30Str}&end_date=${end}`, {
    statusCode: 200,
    body: {
      accountId: account,
      asOfDate: '2025-08-03',
      balances: [
        { date: '2025-08-01', balance: 50 },
        { date: '2025-08-02', balance: 75 },
      ],
    },
  }).as('hist30')

  cy.intercept('GET', `/api/accounts/${account}/history?start_date=${start90Str}&end_date=${end}`, {
    statusCode: 200,
    body: { accountId: account, asOfDate: '2025-08-03', balances: [] },
  }).as('hist90')

  cy.intercept('GET', `/api/transactions/${account}/transactions*`, {
    statusCode: 200,
    body: {
      status: 'success',
      data: { transactions: [{ transaction_id: 't1', amount: -20, description: 'Coffee' }] },
    },
  }).as('tx')

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/accounts/:accountId', component: Accounts }],
  })

  router.push(`/accounts/${account}`)

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

  return cy.wrap(router.isReady()).then(() => cy.wait('@net').wait('@tx').wait(expected))
}

describe('Accounts summary', () => {
  it('shows net change totals and transactions', () => {
    mountPage()
    cy.contains('Income').should('contain', '$1,000.00')
    cy.contains('Expense').should('contain', '$400.00')
    cy.contains('Net').should('contain', '$600.00')
    cy.get('table').should('exist')
    cy.contains('Coffee')
    cy.get('[data-testid="history-chart"]').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Transactions').click()
    cy.get('transactionstable-stub').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Charts').click()
    cy.get('netyearcomparisonchart-stub').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Accounts').click()
    cy.get('accountstable-stub').should('exist')
    cy.get('[data-testid="history-range-select"]').select('90d')
    cy.wait('@hist90')
  })

  it('persists selected range after reload', () => {
    mountPage()
    cy.get('[data-testid="history-range-select"]').select('90d')
    cy.wait('@hist90')
    cy.reload()
    mountPage('acc1', '@hist90', false)
    cy.get('[data-testid="history-range-select"]').should('have.value', '90d')
  })

  it('restores range when switching accounts', () => {
    mountPage('acc1')
    cy.get('[data-testid="history-range-select"]').select('90d')
    cy.wait('@hist90')
    mountPage('acc2', '@hist30', false)
    cy.get('[data-testid="history-range-select"]').should('have.value', '30d')
    mountPage('acc1', '@hist90', false)
    cy.get('[data-testid="history-range-select"]').should('have.value', '90d')
  })
})
