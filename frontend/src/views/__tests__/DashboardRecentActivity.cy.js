import Dashboard from '../Dashboard.vue'

function mountDashboard() {
  cy.intercept('GET', '/api/charts/net_assets', {
    statusCode: 200,
    body: { status: 'success', data: [{ date: '2024-01-01', net_assets: 0 }] },
  })
  cy.intercept('GET', '/api/accounts/get_accounts*', {
    statusCode: 200,
    body: { status: 'success', accounts: [{ account_id: '1', name: 'Checking' }] },
  })
  cy.intercept('GET', '/api/accounts/1/net_changes*', {
    statusCode: 200,
    body: { status: 'success', data: { income: 100, expense: -40, net: 60 } },
  }).as('getNetChanges')
  cy.intercept('GET', '/api/transactions/1/transactions*', {
    statusCode: 200,
    body: {
      status: 'success',
      data: {
        transactions: [
          { transaction_id: 't1', date: '2024-01-01', description: 'Paycheck', amount: 100 },
        ],
      },
    },
  }).as('getRecent')

  cy.mount(Dashboard, {
    global: {
      stubs: {
        AppLayout: true,
        BaseCard: true,
        PaginationControls: true,
        DailyNetChart: true,
        CategoryBreakdownChart: true,
        AccountsTable: true,
        TransactionsTable: true,
        TransactionModal: true,
        AccountSnapshot: true,
      },
    },
  })
  cy.wait(['@getNetChanges', '@getRecent'])
}

describe('Dashboard recent activity', () => {
  it('displays summary and transactions', () => {
    mountDashboard()
    cy.contains('Income').next().should('contain', '$100.00')
    cy.contains('Expenses').next().should('contain', '-$40.00')
    cy.contains('Net').next().should('contain', '$60.00')
    cy.get('table tbody tr').should('have.length', 1)
  })
})
