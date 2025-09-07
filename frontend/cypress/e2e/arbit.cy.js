// arbit.cy.js - Arbit dashboard navigation test

describe('Arbit dashboard link', () => {
  it('navigates to dashboard when enabled', () => {
    cy.intercept('GET', '**/api/**', {})
    cy.intercept('GET', '**/api/arbit/status', {
      running: true,
      config: { enable_arbit_dashboard: true },
    }).as('arbitStatus')

    cy.visit('/')
    cy.wait('@arbitStatus')
    cy.contains('Arbit').click()
    cy.url().should('include', '/arbit')
    cy.contains('Arbit Dashboard')
  })
})
