import AccountsReorderChart from '../AccountsReorderChart.vue'

describe('AccountsReorderChart', () => {
  it('renders assets and liabilities with different classes and shows values on hover', () => {
    cy.intercept('GET', '/api/accounts/get_accounts*', {
      statusCode: 200,
      body: {
        status: 'success',
        accounts: [
          {
            id: 1,
            name: 'Checking',
            subtype: 'checking',
            balance: 500,
            adjusted_balance: 500,
            is_hidden: false,
          },
          {
            id: 2,
            name: 'Credit Card',
            subtype: 'credit card',
            balance: -250,
            adjusted_balance: -250,
            is_hidden: false,
          },
        ],
      },
    }).as('getAccounts')

    cy.mount(AccountsReorderChart)
    cy.wait('@getAccounts')

    cy.get('.asset-bar').should('have.length', 1)
    cy.get('.liability-bar').should('have.length', 1)

    cy.get('.asset-bar').first().trigger('mouseover')
    cy.get('.asset-bar .bar-value').first().should('contain', '$500.00')

    cy.get('.liability-bar').first().trigger('mouseover')
    cy.get('.liability-bar .bar-value').first().should('contain', '-$250.00')
  })
})
