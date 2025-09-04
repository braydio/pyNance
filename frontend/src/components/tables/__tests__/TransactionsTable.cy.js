// TransactionsTable.cy.js - Cypress component tests for filters and pagination
import { mount } from 'cypress/vue'
import TransactionsTable from '../TransactionsTable.vue'

describe('TransactionsTable', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/accounts/get_accounts', {
      statusCode: 200,
      body: { status: 'success', accounts: [{ account_id: 'a1', name: 'Checking' }] },
    })
  })

  it('applies account and type filters', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', (req) => {
      if (req.query.account_ids) {
        expect(req.query.account_ids).to.eq('a1')
        expect(req.query.tx_type).to.eq('debit')
      }
      req.reply({
        statusCode: 200,
        body: { status: 'success', data: { transactions: [], total: 0 } },
      })
    }).as('fetchTx')

    mount(TransactionsTable)
    cy.wait('@fetchTx')
    cy.get('[data-test="account-filter"]').select('a1')
    cy.get('[data-test="type-filter"]').select('debit')
    cy.wait('@fetchTx')
  })

  it('paginates results', () => {
    cy.intercept('GET', '/api/transactions/get_transactions*', (req) => {
      req.reply({
        statusCode: 200,
        body: { status: 'success', data: { transactions: [], total: 0 } },
      })
    }).as('fetchTx')

    mount(TransactionsTable)
    cy.wait('@fetchTx')
    cy.get('[data-test="next-page"]').click()
    cy.wait('@fetchTx').its('request.url').should('include', 'page=2')
  })
})
