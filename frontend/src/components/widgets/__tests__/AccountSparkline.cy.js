/**
 * Component test for AccountSparkline.
 * Ensures a single data point renders without errors.
 */
import AccountSparkline from '../AccountSparkline.vue'

describe('AccountSparkline', () => {
  it('renders single-point history without crashing', () => {
    cy.intercept('GET', '/accounts/123/history*', {
      statusCode: 200,
      body: {
        status: 'success',
        history: [{ date: '2024-01-01', balance: 100 }],
      },
    }).as('getHistory')

    cy.mount(AccountSparkline, { props: { accountId: '123' } })
    cy.wait('@getHistory')
    cy.get('svg polyline')
      .should('have.attr', 'points')
      .and('match', /^0,100$/)
  })
})
