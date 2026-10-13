import { defineComponent, h, ref } from 'vue'
import LinkAccount from '@/components/forms/LinkAccount.vue'

const makeWrapper = (initial = []) =>
  defineComponent({
    setup() {
      const selectedProducts = ref(initial)
      return () =>
        h(
          'div',
          { class: 'glass', style: 'width: 18rem; backdrop-filter: blur(8px); overflow: hidden' },
          [
            h(LinkAccount, {
              selectedProducts: selectedProducts.value,
              'onUpdate:selectedProducts': (products) => {
                selectedProducts.value = products
              },
              onRefreshAccount: () => {},
            }),
          ],
        )
    },
  })

const LinkProviderLauncherStub = defineComponent({
  emits: ['error'],
  setup(_, { emit, slots }) {
    const trigger = () =>
      emit('error', {
        code: 'LINK_TOKEN_GENERATION_FAILED',
        message: 'Unable to generate a link token. Please try again.',
      })
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

const openDialog = () => cy.contains('button', 'Link Account').click()

describe('LinkAccount', () => {
  it('gates the CTA on a product selection', () => {
    cy.mount(makeWrapper())
    openDialog()

    cy.contains('h3', 'Choose what to sync').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.disabled')
    cy.contains('button', 'Transactions').click()
    cy.contains('Selected: Transactions').should('be.visible')
    cy.contains('button', 'Link With Selected Scope').should('be.enabled')
  })

  it('renders inline launcher errors and supports retry', () => {
    cy.mount(makeWrapper(['transactions']), {
      global: { stubs: { LinkProviderLauncher: LinkProviderLauncherStub } },
    })
    openDialog()
    cy.contains('button', 'Link With Selected Scope').click()
    cy.get('[data-testid="launcher-error-message"]')
      .should('be.visible')
      .and('contain.text', 'Unable to generate a link token. Please try again.')
    cy.get('[role="dialog"]').should('exist')
    cy.contains('button', 'Retry').click()
    cy.get('[data-testid="launcher-error-message"]').should('not.exist')
  })

  it('teleports the dialog to body, outside the filtered card', () => {
    cy.mount(makeWrapper())
    openDialog()
    cy.get('.link-dialog-backdrop')
      .should('exist')
      .then(($el) => {
        expect($el[0].closest('body')).to.equal(document.body)
        expect($el[0].closest('[data-cy-root]')).to.equal(null)
        expect($el[0].closest('.glass')).to.equal(null)
      })
  })

  const viewports = [
    [360, 640],
    [390, 844],
    [768, 1024],
    [1440, 900],
    [1280, 600],
  ]
  viewports.forEach(([w, h]) => {
    it(`keeps the dialog in bounds and actions reachable at ${w}x${h}`, () => {
      cy.viewport(w, h)
      cy.mount(makeWrapper())
      openDialog()
      cy.get('.link-dialog-backdrop').then(($b) => {
        const r = $b[0].getBoundingClientRect()
        expect(Math.round(r.width)).to.be.at.least(w - 1)
        expect(Math.round(r.height)).to.be.at.least(h - 1)
      })
      cy.get('.link-dialog').then(($d) => {
        const r = $d[0].getBoundingClientRect()
        expect(r.left).to.be.at.least(0)
        expect(r.right).to.be.at.most(w)
      })
      cy.window().then((win) => {
        expect(win.document.documentElement.scrollWidth).to.be.at.most(w)
      })
      cy.contains('button', 'Liabilities').scrollIntoView().should('be.visible')
      cy.contains('button', 'Cancel').scrollIntoView().should('be.visible')
    })
  })

  it('traps focus, closes on Escape, restores focus and body scroll', () => {
    cy.mount(makeWrapper())
    cy.contains('button', 'Link Account').as('opener').click()
    cy.get('body').should('have.css', 'overflow', 'hidden')
    cy.focused().should('have.attr', 'aria-label', 'Close link dialog')

    cy.get('[role="dialog"]').find('button:not([disabled])').last().focus()
    cy.get('body').type('{esc}')
    cy.get('[role="dialog"]').should('not.exist')
    cy.get('body').should('not.have.css', 'overflow', 'hidden')
    cy.get('@opener').should('have.focus')
  })

  it('restores body scroll when unmounted while open', () => {
    const Host = defineComponent({
      setup() {
        const show = ref(true)
        window.__hide = () => (show.value = false)
        return () => (show.value ? h(LinkAccount, { selectedProducts: [] }) : h('div'))
      },
    })
    cy.mount(Host)
    openDialog()
    cy.get('body').should('have.css', 'overflow', 'hidden')
    cy.window().then((win) => win.__hide())
    cy.get('body').should('not.have.css', 'overflow', 'hidden')
  })
})
