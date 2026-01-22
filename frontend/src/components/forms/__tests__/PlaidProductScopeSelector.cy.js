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

    cy.contains('Choose data to share').should('be.visible')
    cy.contains('Transactions').should('be.visible')
    cy.contains('Share account balances and transaction history for cash flow insights.').should(
      'be.visible',
    )
    cy.contains('Investments').should('be.visible')
    cy.contains('Share holdings and investment activity to track performance.').should('be.visible')
    cy.contains('Liabilities').should('be.visible')
    cy.contains('Share loan and credit details to monitor debts.').should('be.visible')

    cy.contains('button', 'Transactions').click().should('have.attr', 'aria-pressed', 'true')
    cy.contains('button', 'Transactions').click().should('have.attr', 'aria-pressed', 'false')
  })
})
