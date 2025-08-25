// dashboard.cy.js - dashboard feature tests

describe('Dashboard widgets', () => {
  it('renders recent transactions', () => {
    cy.intercept('GET', '/api/charts/daily_net*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/charts/category_breakdown_tree*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/transactions/top_merchants*', { data: [] })
    cy.intercept('GET', '/api/transactions/top_categories*', { data: [] })
    cy.intercept('GET', '/api/transactions/get_transactions*', {
      status: 'success',
      data: {
        transactions: [
          { id: 1, date: '2024-01-01', name: 'Coffee', amount: -5 },
          { id: 2, date: '2024-01-02', name: 'Salary', amount: 500 },
        ],
      },
    }).as('recentTx')

    cy.visit('/')
    cy.wait('@recentTx')

    cy.contains('Recent Transactions').parent().within(() => {
      cy.contains('Coffee')
      cy.contains('Salary')
    })
  })

  it('propagates date range to charts', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', { status: 'success', data: { transactions: [] } })
    cy.intercept('GET', '/api/transactions/top_merchants*', { data: [] })
    cy.intercept('GET', '/api/transactions/top_categories*', { data: [] })
    cy.intercept('GET', '/api/charts/daily_net*', { status: 'success', data: [] }).as('dailyNet')
    cy.intercept('GET', '/api/charts/category_breakdown_tree*', { status: 'success', data: [] }).as('catTree')

    cy.visit('/')
    cy.wait('@dailyNet')
    cy.wait('@catTree')

    cy.get('input[type="date"]').first().clear()
    cy.get('input[type="date"]').first().type('2024-01-01')
    cy.get('input[type="date"]').eq(1).clear()
    cy.get('input[type="date"]').eq(1).type('2024-01-31')

    cy.wait('@dailyNet').its('request.query').should('include', {
      start_date: '2024-01-01',
      end_date: '2024-01-31',
    })
    cy.wait('@catTree').its('request.query').should('include', {
      start_date: '2024-01-01',
      end_date: '2024-01-31',
    })
  })

  it('shows financial summary metrics', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', { status: 'success', data: { transactions: [] } })
    cy.intercept('GET', '/api/transactions/top_merchants*', { data: [] })
    cy.intercept('GET', '/api/transactions/top_categories*', { data: [] })
    cy.intercept('GET', '/api/charts/category_breakdown_tree*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/charts/daily_net*', {
      status: 'success',
      data: [
        {
          date: '2024-01-01',
          income: { parsedValue: 100 },
          expenses: { parsedValue: -50 },
          net: { parsedValue: 50 },
        },
        {
          date: '2024-01-02',
          income: { parsedValue: 200 },
          expenses: { parsedValue: -100 },
          net: { parsedValue: 100 },
        },
      ],
    }).as('dailyNet')

    cy.visit('/')
    cy.wait('@dailyNet')

    cy.get('.stat-income .stat-value').should('contain', '$300.00')
    cy.get('.stat-expenses .stat-value').should('contain', '($150.00)')
    cy.get('.stat-net .stat-value').should('contain', '$150.00')
  })

  it('filters categories via dropdown', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', { status: 'success', data: { transactions: [] } })
    cy.intercept('GET', '/api/transactions/top_merchants*', { data: [] })
    cy.intercept('GET', '/api/transactions/top_categories*', { data: [] })
    cy.intercept('GET', '/api/charts/daily_net*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/charts/category_breakdown_tree*', {
      status: 'success',
      data: [
        {
          id: 'g1',
          label: 'Food',
          amount: 80,
          children: [
            { id: 1, label: 'Groceries', amount: 50 },
            { id: 2, label: 'Dining', amount: 30 },
          ],
        },
        {
          id: 'g2',
          label: 'Utilities',
          amount: 20,
          children: [{ id: 3, label: 'Electricity', amount: 20 }],
        },
      ],
    }).as('catTree')

    cy.visit('/')
    cy.wait('@catTree')

    cy.contains('Spending by Category').parent().parent().within(() => {
      cy.contains('Total:').next().should('contain', '$100.00')
    })

    cy.get('.dropdown-trigger').click()
    cy.get('.dropdown-menu').contains('Dining').click()

    cy.contains('Spending by Category').parent().parent().within(() => {
      cy.contains('Total:').next().should('contain', '$70.00')
    })
  })

  it('displays spending insights data', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', { status: 'success', data: { transactions: [] } })
    cy.intercept('GET', '/api/charts/daily_net*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/charts/category_breakdown_tree*', { status: 'success', data: [] })
    cy.intercept('GET', '/api/transactions/top_merchants*', {
      data: [{ name: 'Store A', total: 50, trend: [1, 2, 3] }],
    }).as('topMerchants')
    cy.intercept('GET', '/api/transactions/top_categories*', {
      data: [{ name: 'Food', total: 70, trend: [3, 2, 1] }],
    }).as('topCategories')

    cy.visit('/')
    cy.wait('@topMerchants')
    cy.wait('@topCategories')

    cy.contains('Top Merchants').parent().should('contain', 'Store A')
    cy.contains('Top Categories').parent().should('contain', 'Food')
  })
})
