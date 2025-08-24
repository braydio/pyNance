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
})

