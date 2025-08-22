import Accounts from '../Accounts.vue'

function mountPage() {
  cy.intercept('GET', '/api/accounts/acc1/net_changes*', {
    statusCode: 200,
    body: { status: 'success', data: { income: 1000, expense: -400, net: 600 } },
  }).as('net')

  cy.intercept('GET', '/api/accounts/acc1/history?range=30d', {
    statusCode: 200,
    body: { accountId: 'acc1', asOfDate: '2025-08-03', balances: [
      { date: '2025-08-01', balance: 50 },
      { date: '2025-08-02', balance: 75 }
    ] }
  }).as('hist30')

  cy.intercept('GET', '/api/accounts/acc1/history?range=90d', {
    statusCode: 200,
    body: { accountId: 'acc1', asOfDate: '2025-08-03', balances: [] }
  }).as('hist90')

  cy.intercept('GET', '/api/transactions/acc1/transactions*', {
    statusCode: 200,
    body: { status: 'success', data: { transactions: [
      { transaction_id: 't1', amount: -20, description: 'Coffee' }
    ] } },
  }).as('tx')

  cy.mount(Accounts, {
    global: {
      stubs: {
        LinkAccount: true,
        RefreshPlaidControls: true,
        RefreshTellerControls: true,
        TokenUpload: true,
        NetYearComparisonChart: true,
        AssetsBarTrended: true,
        AccountsReorderChart: true,
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
    cy.get('[data-testid="filter-dropdown"]').select('90d')
    cy.wait('@hist90')
  })
})
