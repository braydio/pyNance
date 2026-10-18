// financial-workflows-gate.cy.js - TP-20261016-011 post-feature gate for /accounts, /transactions, /forecast.
// All API traffic is mocked; no live Plaid or paid vendor calls. Requires the app served with
// VITE_USER_ID_PLAID set (any non-empty value), like forecast-v2.cy.js.

const VIEWPORTS = [
  [390, 844],
  [768, 1024],
  [1280, 800],
]
const THEMES = ['nightfox', 'everforest-light']
const ROUTES = ['/accounts', '/transactions', '/forecast']
const LONG_INSTITUTION =
  'The First National Cooperative Savings and Credit Union of Greater Cypress County'

const accounts = [
  {
    account_id: 'chk1',
    name: 'Primary Checking',
    institution_name: LONG_INSTITUTION,
    type: 'depository',
    subtype: 'checking',
    status: 'active',
    link_type: 'plaid',
    balance: 4200,
    is_hidden: false,
  },
]

function mockApi(mode) {
  const fail = mode === 'error'
  const empty = mode === 'empty'
  cy.intercept(
    'GET',
    '/api/accounts/get_accounts*',
    fail ? { statusCode: 500, body: {} } : { status: 'success', accounts: empty ? [] : accounts },
  )
  cy.intercept(
    'GET',
    '/api/transactions/get_transactions*',
    fail
      ? { statusCode: 500, body: {} }
      : { status: 'success', data: { transactions: [], total: 0 } },
  )
  cy.intercept(
    'GET',
    '/api/forecast/**',
    fail
      ? { statusCode: 500, body: {} }
      : { statusCode: 200, body: { model_version: 'v2', status: 'ok', timeline: [], summary: {} } },
  )
}

describe('Financial workflows gate', () => {
  VIEWPORTS.forEach(([width, height]) => {
    THEMES.forEach((theme) => {
      ;['data', 'empty', 'error'].forEach((mode) => {
        ROUTES.forEach((route) => {
          it(`${route} ${width}px ${theme} ${mode}: renders without document horizontal scroll`, () => {
            cy.viewport(width, height)
            mockApi(mode)
            cy.visit(route, {
              onBeforeLoad(win) {
                win.localStorage.setItem('pynance-theme', theme)
              },
            })
            cy.get('body').should('be.visible')
            cy.document().then((doc) => {
              const root = doc.documentElement
              expect(root.scrollWidth, 'document scrollWidth').to.be.at.most(root.clientWidth + 1)
            })
            cy.get('html').should('have.attr', 'data-theme', theme)
          })
        })
      })
    })
  })

  it('moves keyboard focus onto an interactive control on each route', () => {
    ROUTES.forEach((route) => {
      mockApi('data')
      cy.visit(route)
      cy.get('button:visible, a[href]:visible, input:visible, select:visible').first().focus()
      cy.focused().should('exist')
    })
  })
})
