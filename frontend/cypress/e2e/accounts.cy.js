// accounts.cy.js
// Cypress E2E test to verify accounts control bar alignment with table header

describe('Accounts control bar', () => {
  it('aligns with the table header', () => {
    cy.intercept('GET', '/api/accounts/get_accounts*', { status: 'success', accounts: [] }).as('getAccounts')
    cy.visit('/accounts/table')
    cy.wait('@getAccounts')
    cy.get('[data-testid="accounts-control-bar"]').then(($bar) => {
      const rectBar = $bar[0].getBoundingClientRect()
      cy.get('table thead').then(($head) => {
        const rectHead = $head[0].getBoundingClientRect()
        expect(Math.abs(rectBar.right - rectHead.right)).to.be.lessThan(2)
        expect(Math.abs(rectBar.left - rectHead.left)).to.be.lessThan(2)
      })
    })
  })
})
