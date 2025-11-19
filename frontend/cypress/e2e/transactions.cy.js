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

  it('applies filters to API calls and resets pagination', () => {
    cy.intercept('GET', '/api/accounts/get_accounts', {
      status: 'success',
      accounts: [{ account_id: 'a1', name: 'Checking' }],
    })
    cy.intercept('GET', '/api/transactions/get_transactions*', (req) => {
      const page = Number(req.query.page || 1)
      req.alias = 'getTx'
      req.reply({
        status: 'success',
        data: {
          transactions: Array.from({ length: 10 }, (_, index) => ({
            transaction_id: `tx-${page}-${index}`,
            date: '2024-01-01',
            amount: 12.34,
            description: `Transaction ${page}-${index}`,
            category: 'General',
            merchant_name: 'Merchant',
            account_name: 'Checking',
            institution_name: 'Bank',
            subtype: 'checking',
          })),
          total: 25,
        },
      })
    })

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

    // Move to next page to ensure pagination is wired
    cy.contains('#pagination-controls button', 'Next').click()
    cy.wait('@getTx').its('request.query').should('include', { page: '2' })

    // Changing filters should reset the pagination back to page 1
    cy.get('[data-testid="type-select"]').select('debit')
    cy.wait('@getTx').its('request.query').should('include', {
      tx_type: 'debit',
      page: '1',
    })
  })
})
