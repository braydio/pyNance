import Accounts from '../Accounts.vue'

function mountPage() {
  const today = new Date()
  const end = today.toISOString().slice(0, 10)

  const start30 = new Date(today)
  start30.setDate(start30.getDate() - 30)
  const start30Str = start30.toISOString().slice(0, 10)

  const start90 = new Date(today)
  start90.setDate(start90.getDate() - 90)
  const start90Str = start90.toISOString().slice(0, 10)

  cy.intercept('GET', '/api/accounts/acc1/net_changes*', {
    statusCode: 200,
    body: { status: 'success', data: { income: 1000, expense: -400, net: 600 } },
  }).as('net')

  cy.intercept('GET', `/api/accounts/acc1/history?start_date=${start30Str}&end_date=${end}`, {
    statusCode: 200,
    body: {
      accountId: 'acc1',
      asOfDate: '2025-08-03',
      balances: [
        { date: '2025-08-01', balance: 50 },
        { date: '2025-08-02', balance: 75 },
      ],
    },
  }).as('hist30')

  cy.intercept('GET', `/api/accounts/acc1/history?start_date=${start90Str}&end_date=${end}`, {
    statusCode: 200,
    body: { accountId: 'acc1', asOfDate: '2025-08-03', balances: [] },
  }).as('hist90')

  cy.intercept('GET', '/api/transactions/acc1/transactions*', {
    statusCode: 200,
    body: {
      status: 'success',
      data: { transactions: [{ transaction_id: 't1', amount: -20, description: 'Coffee' }] },
    },
  }).as('tx')

  cy.mount(Accounts, {
    global: {
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

  return cy.wait('@net').wait('@tx').wait('@hist30')
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
    cy.get('[data-testid="history-range-controls"] button').contains('90d').click()
    cy.wait('@hist90')
  })
})
