import LinkAccount from '@/components/forms/LinkAccount.vue'

/**
 * Open the LinkAccount modal dialog.
 */
const openDialog = () => {
  cy.contains('button', 'Link a New Account with Plaid').click()
}

describe('LinkAccount', () => {
  it('renders the two-step flow with selection summary and disabled CTA', () => {
    cy.mount(LinkAccount)

    openDialog()

    cy.contains('Step 1').should('be.visible')
    cy.contains('Choose product scope').should('be.visible')
    cy.contains('Step 2').should('be.visible')
    cy.contains('Connect with Plaid').should('be.visible')

    cy.contains('Selected: Transactions').should('be.visible')
    cy.contains('Each account link requires at least one product scope.').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.enabled')

    cy.contains('button', 'Transactions').click()

    cy.contains('Selected: Transactions').should('not.exist')
    cy.contains('button', 'Link With Selected Scope').should('be.disabled')
  })
})
