// dashboard.cy.js
// Cypress E2E tests for Dashboard features

describe('Dashboard view', () => {
  beforeEach(() => {
    // Stub recent transactions
    cy.intercept('GET', '/api/transactions/get_transactions*', {
      statusCode: 200,
      body: {
        transactions: [
          { id: 1, date: '2024-01-01', name: 'Coffee', amount: -3.5 },
          { id: 2, date: '2024-01-02', name: 'Salary', amount: 5000 },
          { id: 3, date: '2024-01-03', name: 'Groceries', amount: -50 },
        ],
      },
    }).as('recentTx')

    // Stub chart data
    cy.intercept('GET', '/api/charts/daily_net*', (req) => {
      req.reply({
        status: 'success',
        data: [
          {
            date: '2024-01-01',
            income: { parsedValue: 200 },
            expenses: { parsedValue: -50 },
            net: { parsedValue: 150 },
          },
        ],
      })
    }).as('dailyNet')

    cy.intercept('GET', '/api/charts/category_breakdown_tree*', (req) => {
      req.reply({ status: 'success', data: [] })
    }).as('catBreakdown')

    // Stub category groups for dropdown
    cy.intercept('GET', '/api/categories/tree*', {
      statusCode: 200,
      body: {
        status: 'success',
        data: [
          { id: 1, label: 'Food', children: [{ id: 10, label: 'Groceries' }] },
        ],
      },
    }).as('categoriesTree')

    // Stub spending insights
    cy.intercept('GET', '/api/transactions/top_merchants*', {
      statusCode: 200,
      body: { data: [{ name: 'Amazon', total: 100, trend: [1, 2, 3] }] },
    }).as('topMerchants')
    cy.intercept('GET', '/api/transactions/top_categories*', {
      statusCode: 200,
      body: { data: [{ name: 'Food', total: 50, trend: [1, 2, 3] }] },
    }).as('topCategories')
  })

  it('renders recent transactions', () => {
    cy.visit('/')
    cy.wait('@recentTx')
    cy.contains('Recent Transactions')
    cy.contains('Coffee')
    cy.contains('Salary')
  })

  it('propagates date range to charts', () => {
    cy.visit('/')
    cy.wait(['@dailyNet', '@catBreakdown'])
    cy.get('input[type="date"]').first().clear()
    cy.get('input[type="date"]').first().type('2024-01-01')
    cy.wait('@dailyNet')
    cy.get('input[type="date"]').eq(1).clear()
    cy.get('input[type="date"]').eq(1).type('2024-01-31')
    cy.wait('@dailyNet').its('request.url').should('include', 'start_date=2024-01-01').and('include', 'end_date=2024-01-31')
    cy.wait('@catBreakdown').its('request.url').should('include', 'start_date=2024-01-01').and('include', 'end_date=2024-01-31')
  })

  it('displays financial summary metrics', () => {
    cy.visit('/')
    cy.wait('@dailyNet')
    cy.contains('.stat-income .stat-value', '$200.00')
    cy.contains('.stat-expenses .stat-value', '($50.00)')
    cy.contains('.stat-net .stat-value', '$150.00')
  })

  it('filters categories on chart', () => {
    cy.visit('/')
    cy.wait('@catBreakdown')
    cy.get('.dropdown-trigger').click()
    cy.contains('label', 'Groceries').find('input').check({ force: true })
    cy.wait('@catBreakdown').its('request.url').should('include', 'category_ids=10')
  })

  it('shows spending insights', () => {
    cy.visit('/')
    cy.wait(['@topMerchants', '@topCategories'])
    cy.contains('Top Merchants').parent().should('contain', 'Amazon')
    cy.contains('Top Categories').parent().should('contain', 'Food')
  })
})
