// transactions.cy.js - tests for transactions view

describe('Transactions View', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/accounts/get_accounts', {
      status: 'success',
      accounts: [{ account_id: 'a1', name: 'Checking' }],
    })

    cy.intercept('GET', '/api/transactions/get_transactions*', (req) => {
      req.reply({
        statusCode: 200,
        body: { status: 'success', data: { transactions: [], total: 0 } },
      })
    }).as('getTx')
  })

  it('navigates tabs and opens scanner from the sidebar', () => {
    cy.visit('/transactions')
    cy.wait('@getTx')

    cy.get('[data-testid="transactions-activity-panel"]').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Recurring').click()
    cy.contains('Recurring Transactions').should('exist')

    cy.get('[data-testid="tabbed-nav"]').contains('Activity').click()
    cy.get('[data-testid="open-scanner"]').click()
    cy.get('[data-testid="scanner-panel"]').should('exist')
  })

  it('applies filters to API calls', () => {
    cy.visit('/transactions')
    cy.wait('@getTx')

    cy.get('[data-testid="transactions-search"]').type('rent')

    // Date range filter
    cy.get('input[type="date"]').first().type('2024-01-01')
    cy.get('input[type="date"]').eq(1).type('2024-01-31')
    cy.wait('@getTx').its('request.query').should('include', {
      start_date: '2024-01-01',
      end_date: '2024-01-31',
    })

    // Account filter
    cy.get('[data-testid="account-select"]').select('a1')
    cy.wait('@getTx').its('request.query').should('include', {
      account_ids: 'a1',
    })

    // Type filter
    cy.get('[data-testid="type-select"]').select('credit')
    cy.wait('@getTx').its('request.query').should('include', {
      tx_type: 'credit',
    })
  })
})
