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
    cy.contains('button', 'Next ›').click()
    cy.wait('@fetchTx').its('request.url').should('include', 'page=2')
  })

  it('keeps account filters applied across pagination without empty rows', () => {
    const pageData = {
      1: [
        { transaction_id: 'p1', date: '2024-01-01', category: 'Food', description: 'Coffee' },
        { transaction_id: 'p2', date: '2024-01-02', category: 'Bills', description: 'Rent' },
      ],
      2: [
        { transaction_id: 'p3', date: '2024-01-03', category: 'Travel', description: 'Train' },
        { transaction_id: 'p4', date: '2024-01-04', category: 'Income', description: 'Paycheck' },
      ],
    }

    cy.intercept('GET', '/api/transactions/get_transactions*', (req) => {
      const page = Number(req.query.page || '1')
      req.reply({
        statusCode: 200,
        body: {
          status: 'success',
          data: { transactions: pageData[page], total: 4 },
        },
      })
    }).as('fetchFilteredPages')

    mount(TransactionsTable)
    cy.wait('@fetchFilteredPages')
    cy.get('[data-test="account-filter"]').select('a1')
    cy.wait('@fetchFilteredPages')
      .its('request.url')
      .should('include', 'account_ids=a1')
    cy.contains('td', 'Coffee').should('be.visible')

    cy.contains('button', 'Next ›').click()
    cy.wait('@fetchFilteredPages').then(({ request }) => {
      expect(request.url).to.include('account_ids=a1')
      expect(request.url).to.include('page=2')
    })
    cy.contains('td', 'Train').should('be.visible')
    cy.contains('td', 'Paycheck').should('be.visible')
  })
})
