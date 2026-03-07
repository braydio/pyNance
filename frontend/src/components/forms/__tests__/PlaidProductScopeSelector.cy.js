import PlaidProductScopeSelector from '@/components/forms/PlaidProductScopeSelector.vue'

describe('PlaidProductScopeSelector', () => {
  it('renders helper text and toggles product selection', () => {
    cy.mount({
      components: { PlaidProductScopeSelector },
      template: '<PlaidProductScopeSelector v-model="modelValue" />',
      data() {
        return {
          modelValue: [],
        }
      },
    })

    cy.contains('Choose what data to share').should('be.visible')
    cy.get('legend').should('have.text', 'Choose what data to share')
    cy.get('[role="group"]').should('have.attr', 'aria-label', 'Choose what data to share')
    cy.contains('Transactions').should('be.visible')
    cy.contains('Enables account balances and transaction history for cash flow insights.').should(
      'be.visible',
    )
    cy.contains('Investments').should('be.visible')
    cy.contains('Enables holdings and investment activity tracking in your portfolio views.').should(
      'be.visible',
    )
    cy.contains('Liabilities').should('be.visible')
    cy.contains('Enables loan and credit detail tracking for debt monitoring.').should('be.visible')

    cy.contains('button', 'Transactions').click().should('have.attr', 'aria-pressed', 'true')
    cy.contains('button', 'Transactions').click().should('have.attr', 'aria-pressed', 'false')
  })
})
