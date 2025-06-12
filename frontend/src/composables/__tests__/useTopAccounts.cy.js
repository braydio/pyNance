import { defineComponent } from 'vue'
import { useTopAccounts } from '../useTopAccounts'

const TestComponent = defineComponent({
  template: '<div><div class="row" v-for="acc in positiveAccounts" :key="acc.id">{{ acc.name }}</div></div>',
  setup() {
    const { positiveAccounts } = useTopAccounts()
    return { positiveAccounts }
  },
})

describe('useTopAccounts', () => {
  it('builds account data from API', () => {
    cy.intercept('GET', '/api/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          {
            id: 1,
            name: 'Checking',
            subtype: 'checking',
            balance: 100,
            adjusted_balance: 100,
            is_hidden: false,
          },
        ],
      },
    }).as('getAccounts')

    cy.mount(TestComponent)
    cy.wait('@getAccounts')
    cy.get('.row').should('have.length', 1).and('contain', 'Checking')
  })
})
