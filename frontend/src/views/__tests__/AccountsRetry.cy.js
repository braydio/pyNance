import Accounts from '../Accounts.vue'

function mountWithIntercepts({
  failSummary = false,
  failTransactions = false,
  failHistory = false,
} = {}) {
  let summaryCalls = 0
  let transactionsCalls = 0
  let historyCalls = 0

  const today = new Date()
  const end = today.toISOString().slice(0, 10)
  const start30 = new Date(today)
  start30.setDate(start30.getDate() - 30)
  const start30Str = start30.toISOString().slice(0, 10)

  cy.intercept('GET', '/api/accounts/acc1/net_changes*', (req) => {
    summaryCalls += 1
    if (failSummary && summaryCalls === 1) {
      req.reply({ statusCode: 500, body: {} })
      return
    }

    req.reply({
      statusCode: 200,
      body: { status: 'success', data: { income: 0, expense: 0, net: 0 } },
    })
  }).as('net')

  cy.intercept('GET', '/api/transactions/acc1/transactions*', (req) => {
    transactionsCalls += 1
    if (failTransactions && transactionsCalls === 1) {
      req.reply({ statusCode: 500, body: {} })
      return
    }

    req.reply({ statusCode: 200, body: { status: 'success', data: { transactions: [] } } })
  }).as('tx')

  cy.intercept(
    'GET',
    `/api/accounts/acc1/history?start_date=${start30Str}&end_date=${end}`,
    (req) => {
      historyCalls += 1
      if (failHistory && historyCalls === 1) {
        req.reply({ statusCode: 500, body: {} })
        return
      }

      req.reply({
        statusCode: 200,
        body: { accountId: 'acc1', asOfDate: '2025-08-03', balances: [] },
      })
    },
  ).as('hist')

  cy.mount(Accounts, {
    global: {
      stubs: {
        AccountActionsSidebar: true,
        NetYearComparisonChart: true,
        AssetsBarTrended: true,
        AccountsReorderChart: true,
        AccountsTable: true,
        InstitutionTable: true,
      },
    },
  })

  return cy.wrap({ summaryCalls, transactionsCalls, historyCalls })
}

describe('Accounts retry logic', () => {
  it('retries only failed history query from history retry panel', () => {
    mountWithIntercepts({ failHistory: true })

    cy.wait('@net')
    cy.wait('@tx')
    cy.wait('@hist')
    cy.contains('Failed to load history')

    cy.get('[data-testid="retry-button"]').click()
    cy.wait('@hist')

    cy.get('@net.all').should('have.length', 1)
    cy.get('@tx.all').should('have.length', 1)
    cy.get('@hist.all').should('have.length', 2)
    cy.get('[data-testid="history-chart"]').should('exist')
  })

  it('keeps successful panels and allows top-level refresh to recover failed queries', () => {
    mountWithIntercepts({ failSummary: true, failHistory: true })

    cy.wait('@net')
    cy.wait('@tx')
    cy.wait('@hist')

    cy.contains('Failed to load summary')
    cy.contains('Failed to load history')
    cy.get('table').should('exist')

    cy.contains('button', 'Refresh Overview').click()

    cy.wait('@net')
    cy.wait('@tx')
    cy.wait('@hist')

    cy.contains('Failed to load summary').should('not.exist')
    cy.contains('Failed to load history').should('not.exist')
    cy.get('[data-testid="net-summary-cards"]').should('exist')
    cy.get('[data-testid="history-chart"]').should('exist')
  })
})
