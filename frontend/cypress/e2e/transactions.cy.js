// transactions.cy.js - tests for transactions view

describe('Transactions View', () => {
  it('toggles internal transfer scanner', () => {
    cy.visit('/transactions')

    // Scanner hidden by default
    cy.contains('Internal Transfer Scanner')
    cy.contains('button', 'Show').should('exist')
    cy.contains('Scan').should('not.exist')

    // Show scanner
    cy.contains('button', 'Show').click()
    cy.contains('button', 'Hide').should('exist')
    cy.contains('Scan').should('exist')

    // Hide again
    cy.contains('button', 'Hide').click()
    cy.contains('Scan').should('not.exist')
  })

  it('applies filters to API calls', () => {
    cy.intercept('GET', '/api/accounts/get_accounts', {
      status: 'success',
      accounts: [{ account_id: 'a1', name: 'Checking' }],
    })
    cy.intercept('GET', '/api/transactions/get_transactions*', {
      status: 'success',
      data: { transactions: [], total: 0 },
    }).as('getTx')

    cy.visit('/transactions')
    cy.wait('@getTx')

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
