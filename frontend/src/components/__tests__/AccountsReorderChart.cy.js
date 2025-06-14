import { defineComponent } from 'vue'
import AccountsReorderChart from '../charts/AccountsReorderChart.vue'

const TestWrapper = defineComponent({
  components: { AccountsReorderChart },
  template: '<AccountsReorderChart />',
})

describe('AccountsReorderChart', () => {
  it('shows axis ticks and balances', () => {
    cy.intercept('GET', '/api/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          { id: 1, name: 'Checking', adjusted_balance: 100, is_hidden: false },
        ],
      },
    }).as('getAccounts')

    cy.mount(TestWrapper)
    cy.wait('@getAccounts')
    cy.get('.bar-axis .tick').should('have.length', 5)
    cy.get('.label-balance').first().should('contain', '$100')
  })
})
