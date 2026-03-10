import { defineComponent, h, ref } from 'vue'
import LinkAccount from '@/components/forms/LinkAccount.vue'

const TestWrapper = defineComponent({
  setup() {
    const selectedProducts = ref([])

    return () =>
      h(LinkAccount, {
        selectedProducts: selectedProducts.value,
        'onUpdate:selectedProducts': (products) => {
          selectedProducts.value = products
        },
        onRefreshAccount: () => {},
      })
  },
})

const LinkProviderLauncherStub = defineComponent({
  emits: ['error'],
  setup(_, { emit, slots }) {
    const trigger = () => {
      emit('error', {
        code: 'LINK_TOKEN_GENERATION_FAILED',
        message: 'Unable to generate a link token. Please try again.',
      })
    }

    return () =>
      h('div', [
        slots.default?.({
          linkPlaid: trigger,
          loading: false,
          isDisabled: false,
          statusMessage: '',
        }),
      ])
  },
})

const TestWrapperWithLauncherError = defineComponent({
  setup() {
    const selectedProducts = ref(['transactions'])

    return () =>
      h(LinkAccount, {
        selectedProducts: selectedProducts.value,
        'onUpdate:selectedProducts': (products) => {
          selectedProducts.value = products
        },
        onRefreshAccount: () => {},
      })
  },
})

const openDialog = () => {
  cy.contains('button', 'Link a New Account with Plaid').click()
}

describe('LinkAccount', () => {
  it('renders the two-step flow with selection-first guidance and CTA gating', () => {
    cy.mount(TestWrapper)

    openDialog()

    cy.contains('Step 1').should('be.visible')
    cy.contains('h3', 'Choose data scope').should('be.visible')
    cy.contains('Choose what data to share').should('be.visible')
    cy.contains('Step 2').should('be.visible')
    cy.contains('Connect with Plaid').should('be.visible')

    cy.contains('Selected:').should('not.exist')
    cy.contains('p', 'Choose at least one data scope to continue.').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.disabled')

    cy.contains('button', 'Transactions').click()

    cy.contains('Selected: Transactions').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.enabled')
  })

  it('renders inline launcher errors and supports retry affordance', () => {
    cy.mount(TestWrapperWithLauncherError, {
      global: {
        stubs: {
          LinkProviderLauncher: LinkProviderLauncherStub,
        },
      },
    })

    openDialog()

    cy.contains('button', 'Link With Selected Scope').click()

    cy.get('[data-testid="launcher-error-message"]')
      .should('be.visible')
      .and('contain.text', 'Unable to generate a link token. Please try again.')
    cy.contains('button', 'Retry').click()
    cy.get('[data-testid="launcher-error-message"]').should('not.exist')
    cy.contains('button', 'Link With Selected Scope').should('be.enabled')
  })
})
