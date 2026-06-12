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
          { account_id: '2', name: 'Savings' },
        ],
      },
    }).as('getAccounts')

    mount(RefreshPlaidControls)
    cy.wait('@getAccounts')
    cy.contains('button', 'All Linked Accounts').click()
    cy.get('.dropdown-menu label').should('have.length', 2)
    cy.get('.dropdown-menu').contains('Checking')
    cy.get('.dropdown-menu').contains('Savings')
  })

  it('applies success and error status classes for account pills', () => {
    cy.intercept('GET', '/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          { account_id: '1', name: 'Checking', institution_name: 'Bank A' },
          { account_id: '2', name: 'Savings', institution_name: 'Bank A' },
        ],
      },
    }).as('getAccounts')

    cy.intercept('POST', '/accounts/refresh*', {
      statusCode: 200,
      body: {
        status: 'success',
        refreshed_counts: { 'Bank A': 2 },
        errors: [{ plaid_error_code: 'ITEM_LOGIN_REQUIRED', account_ids: ['2'] }],
      },
    }).as('refreshAccounts')

    mount(RefreshPlaidControls)
    cy.wait('@getAccounts')
    cy.contains('button', 'Sync Account Activity').click()
    cy.wait('@refreshAccounts')

    cy.contains('.account-row', 'Checking').find('.status-pill').should('have.class', 'status-pill--success')
    cy.contains('.account-row', 'Savings').find('.status-pill').should('have.class', 'status-pill--error')
  })
})
