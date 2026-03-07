import { defineComponent, ref } from 'vue'
import LinkAccount from '@/components/forms/LinkAccount.vue'

const TestWrapper = defineComponent({
  components: { LinkAccount },
  setup() {
    const selectedProducts = ref([])

    return {
      selectedProducts,
    }
  },
  template:
    '<LinkAccount v-model:selected-products="selectedProducts" @refresh-account="() => {}" />',
})

/**
 * Open the LinkAccount modal dialog.
 */
const openDialog = () => {
  cy.contains('button', 'Link a New Account with Plaid').click()
}

describe('LinkAccount', () => {
  it('renders the two-step flow with selection-first guidance and CTA gating', () => {
    cy.mount(TestWrapper)

    openDialog()

    cy.contains('Step 1').should('be.visible')

    cy.contains('h3', 'Choose data scope').should('be.visible')
    cy.contains('p', 'Choose data scope').should('be.visible')
    cy.contains('Select an Account Type').should('not.exist')
    cy.contains('classifications').should('not.exist')
    cy.contains('Choose what data to share').should('be.visible')
    cy.contains('Step 2').should('be.visible')
    cy.contains('Connect with Plaid').should('be.visible')

    cy.contains('Selected:').should('not.exist')
    cy.contains('Choose at least one data scope to continue.').should('have.length', 2)
    cy.contains('button', 'Link With Selected Scope').should('be.disabled')

    cy.contains('button', 'Transactions').click()

    cy.contains('Selected: Transactions').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.enabled')
  })
})
