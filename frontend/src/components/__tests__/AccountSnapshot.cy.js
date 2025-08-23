// Cypress component test for AccountSnapshot widget
import { mount } from 'cypress/vue'
import AccountSnapshot from '../widgets/AccountSnapshot.vue'

describe('AccountSnapshot', () => {
  it('expands to show recent transactions when an account is clicked', () => {
    cy.intercept('GET', '**/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          {
            account_id: '1',
            name: 'Checking',
            institution_name: 'Test Bank',
            balance: 1000,
          },
        ],
      },
    }).as('getAccounts')

    cy.intercept('GET', '**/recurring/1/recurring*', {
      statusCode: 200,
      body: {
        status: 'success',
        reminders: [],
      },
    }).as('getReminders')

    cy.intercept('GET', '**/transactions/1/transactions*', {
      statusCode: 200,
      body: {
        transactions: [
          { id: 't1', date: '2024-01-01', name: 'Coffee', amount: -5 },
          { id: 't2', date: '2024-01-02', name: 'Groceries', amount: -20 },
          { id: 't3', date: '2024-01-03', name: 'Salary', amount: 1000 },
        ],
      },
    }).as('getTransactions')

    mount(AccountSnapshot)
    cy.wait(['@getAccounts', '@getReminders'])

    cy.contains('td', 'Checking').click()
    cy.wait('@getTransactions')

    cy.contains('Coffee')
    cy.contains('Groceries')
    cy.contains('Salary')
  })
})
