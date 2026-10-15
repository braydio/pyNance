import RefreshPlaidControls from '../widgets/RefreshPlaidControls.vue'
import clickOutside from '@/directives/clickOutside'
import { mount } from 'cypress/vue'

describe('RefreshPlaidControls', () => {
  it('loads accounts into dropdown', () => {
    cy.intercept('GET', '**/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          { account_id: '1', name: 'Checking' },
          { account_id: '2', name: 'Savings' },
        ],
      },
    }).as('getAccounts')

    mount(RefreshPlaidControls, { global: { directives: { 'click-outside': clickOutside } } })
    cy.wait('@getAccounts')
    cy.contains('button', 'All linked accounts').click()
    cy.get('.dropdown-menu label').should('have.length', 2)
    cy.get('.dropdown-menu').contains('Checking')
    cy.get('.dropdown-menu').contains('Savings')
  })

  it('applies success and error status classes for account pills', () => {
    cy.intercept('GET', '**/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          { account_id: '1', name: 'Checking', institution_name: 'Bank A' },
          { account_id: '2', name: 'Savings', institution_name: 'Bank A' },
        ],
      },
    }).as('getAccounts')

    cy.intercept('POST', '**/accounts/refresh*', {
      statusCode: 200,
      body: {
        status: 'success',
        refreshed_counts: { 'Bank A': 2 },
        errors: [{ plaid_error_code: 'ITEM_LOGIN_REQUIRED', account_ids: ['2'] }],
      },
    }).as('refreshAccounts')

    mount(RefreshPlaidControls, { global: { directives: { 'click-outside': clickOutside } } })
    cy.wait('@getAccounts')
    cy.contains('button', 'Sync Account Activity').click()
    cy.wait('@refreshAccounts')

    cy.contains('.account-row', 'Checking')
      .find('.status-pill')
      .should('have.class', 'status-pill--success')
    cy.contains('.account-row', 'Savings')
      .find('.status-pill')
      .should('have.class', 'status-pill--error')
  })

  it('shows a single reconnect action for an Item with several accounts', () => {
    const status = { provider: 'plaid', state: 'reauth_required', connection_id: 7 }
    cy.intercept('GET', '**/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: ['1', '2', '3'].map((id) => ({
          account_id: id,
          name: `Account ${id}`,
          institution_name: 'Bank A',
          connection_status: status,
        })),
      },
    }).as('getAccounts')

    mount(RefreshPlaidControls, { global: { directives: { 'click-outside': clickOutside } } })
    cy.wait('@getAccounts')
    cy.contains('button', 'Reconnect with Plaid').should('have.length', 1)
    cy.get('[data-testid="reconnect-account-count"]').should('contain', '3 accounts')
  })
})
