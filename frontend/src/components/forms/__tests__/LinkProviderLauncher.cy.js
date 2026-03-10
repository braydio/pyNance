import { defineComponent, h, ref } from 'vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'
import accountLinkApi from '@/api/accounts_link'

const mountLauncher = (props = {}) => {
  const events = []

  const Host = defineComponent({
    components: { LinkProviderLauncher },
    setup() {
      const errorEvents = ref([])
      const pushError = (payload) => {
        errorEvents.value.push(payload)
        events.push(payload)
      }

      return { errorEvents, pushError }
    },
    render() {
      return h(
        LinkProviderLauncher,
        {
          selectedProducts: props.selectedProducts || ['transactions'],
          userId: props.userId || 'user-1',
          onError: this.pushError,
        },
        {
          default: ({ linkPlaid, loading, isDisabled, errorMessage, statusMessage }) =>
            h('div', [
              h(
                'button',
                {
                  disabled: isDisabled,
                  onClick: linkPlaid,
                  'data-testid': 'launcher-cta',
                },
                loading ? statusMessage || 'Loading' : 'Launch',
              ),
              h('p', { 'data-testid': 'slot-error' }, errorMessage || ''),
            ]),
        },
      )
    },
  })

  cy.mount(Host)
  return events
}

describe('LinkProviderLauncher', () => {
  beforeEach(() => {
    cy.stub(accountLinkApi, 'generateLinkToken').resolves({ status: 'success', link_token: 'token-1' })
    cy.stub(accountLinkApi, 'exchangePublicToken').resolves({ status: 'success' })
  })

  afterEach(() => {
    window.Plaid = undefined
  })

  it('emits a structured error when Plaid script load fails', () => {
    const events = mountLauncher()

    cy.window().then((win) => {
      const appendChild = cy.stub(win.document.head, 'appendChild').callsFake((node) => {
        node.onerror(new Error('script failed'))
        return node
      })
      expect(appendChild).to.exist
    })

    cy.get('[data-testid="launcher-cta"]').click()

    cy.get('[data-testid="slot-error"]').should(
      'contain.text',
      'Unable to load Plaid right now. Please refresh and try again.',
    )
    cy.wrap(null).then(() => {
      expect(events[0]).to.deep.equal({
        code: 'PLAID_SCRIPT_LOAD_FAILED',
        message: 'Unable to load Plaid right now. Please refresh and try again.',
      })
    })
  })

  it('emits token generation failures when API returns error status', () => {
    const events = mountLauncher()

    window.Plaid = {
      create: cy.stub().returns({ open: cy.stub() }),
    }

    accountLinkApi.generateLinkToken.restore()
    cy.stub(accountLinkApi, 'generateLinkToken').resolves({ status: 'error', message: 'Token service down' })

    cy.get('[data-testid="launcher-cta"]').click()

    cy.get('[data-testid="slot-error"]').should('contain.text', 'Token service down')
    cy.wrap(null).then(() => {
      expect(events[0]).to.deep.equal({ code: 'LINK_TOKEN_GENERATION_FAILED', message: 'Token service down' })
    })
  })

  it('shows missing token/sdk guard errors', () => {
    const events = mountLauncher()

    window.Plaid = {
      create: cy.stub().returns({ open: cy.stub() }),
    }

    accountLinkApi.generateLinkToken.restore()
    cy.stub(accountLinkApi, 'generateLinkToken').resolves({ status: 'success', link_token: '' })

    cy.get('[data-testid="launcher-cta"]').click()

    cy.get('[data-testid="slot-error"]').should(
      'contain.text',
      'We could not initialize Plaid. Please try again in a moment.',
    )
    cy.wrap(null).then(() => {
      expect(events[0]).to.deep.equal({
        code: 'MISSING_LINK_TOKEN_OR_SDK',
        message: 'We could not initialize Plaid. Please try again in a moment.',
      })
    })
  })

  it('emits exchange failures when public token exchange fails', () => {
    const events = mountLauncher()

    window.Plaid = {
      create: ({ onSuccess }) => ({
        open: () => {
          onSuccess('public-token')
        },
      }),
    }

    accountLinkApi.exchangePublicToken.restore()
    cy.stub(accountLinkApi, 'exchangePublicToken').rejects(new Error('exchange failed'))

    cy.get('[data-testid="launcher-cta"]').click()

    cy.get('[data-testid="slot-error"]').should(
      'contain.text',
      'We could not finish linking the account. Please retry.',
    )
    cy.wrap(null).then(() => {
      expect(events[0]).to.deep.equal({
        code: 'PUBLIC_TOKEN_EXCHANGE_FAILED',
        message: 'We could not finish linking the account. Please retry.',
      })
    })
  })
})
