import RefreshPlaidControls from '../widgets/RefreshPlaidControls.vue'
import { mount } from 'cypress/vue'

describe('RefreshPlaidControls', () => {
  it('loads accounts into dropdown', () => {
    cy.intercept('GET', '/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          { account_id: '1', name: 'Checking' },
          { account_id: '2', name: 'Savings' }
        ]
      }
    }).as('getAccounts')

    mount(RefreshPlaidControls)
    cy.wait('@getAccounts')
    cy.contains('button', 'Select Accounts').click()
    cy.get('.dropdown-menu label').should('have.length', 2)
    cy.get('.dropdown-menu').contains('Checking')
    cy.get('.dropdown-menu').contains('Savings')
  })
})
