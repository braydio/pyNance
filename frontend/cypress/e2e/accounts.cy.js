// accounts.cy.js
// Cypress E2E test to verify accounts control bar alignment with table header

describe('Accounts control bar', () => {
  it('aligns with the table header', () => {
    cy.intercept('GET', '/api/accounts/get_accounts*', { status: 'success', accounts: [] }).as(
      'getAccounts',
    )
    cy.visit('/accounts/table')
    cy.wait('@getAccounts')
    cy.get('[data-testid="accounts-control-bar"]').then(($bar) => {
      const rectBar = $bar[0].getBoundingClientRect()
      cy.get('table thead').then(($head) => {
        const rectHead = $head[0].getBoundingClientRect()
        expect(Math.abs(rectBar.right - rectHead.right)).to.be.lessThan(2)
        expect(Math.abs(rectBar.left - rectHead.left)).to.be.lessThan(2)
      })
    })
  })
})

describe('Account deletion flow', () => {
  it('confirms deletion with a modal and surfaces toast feedback', () => {
    let requestCount = 0
    cy.intercept('GET', '/api/accounts/get_accounts*', (req) => {
      requestCount += 1
      const response =
        requestCount === 1
          ? {
              status: 'success',
              accounts: [
                {
                  account_id: 'acc-123',
                  last_refreshed: '2024-01-01T00:00:00Z',
                  institution_icon_url: '',
                  institution_name: 'Bank of Cypress',
                  name: 'Test Checking',
                  type: 'depository',
                  subtype: 'checking',
                  status: 'active',
                  link_type: 'plaid',
                  balance: 1200,
                  is_hidden: false,
                },
              ],
            }
          : { status: 'success', accounts: [] }
      req.reply(response)
    }).as('getAccounts')

    cy.intercept('DELETE', '/api/plaid/transactions/delete_account', (req) => {
      expect(req.body).to.deep.equal({ account_id: 'acc-123' })
      req.reply({ status: 'success' })
    }).as('deleteAccount')

    cy.visit('/accounts/table')
    cy.wait('@getAccounts')

    cy.contains('button', 'Show Controls').click()
    cy.contains('button', 'Show Delete Buttons').click()
    cy.contains('button', 'Delete').click()

    cy.contains('Delete account?').should('be.visible')
    cy.get('[data-testid="delete-modal-confirm"]').should('be.enabled')
    cy.get('[data-testid="delete-modal-confirm"]').click()

    cy.wait('@deleteAccount')
    cy.wait('@getAccounts')

    cy.get('[data-testid="delete-modal-confirm"]').should('not.exist')
    cy.get('.Vue-Toastification__toast--success').should(
      'contain.text',
      'Account deleted successfully.',
    )
  })
})
