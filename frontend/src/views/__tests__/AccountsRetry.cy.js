import Accounts from '../Accounts.vue'

function mountWithFailingHistory() {
  let call = 0

  cy.intercept('GET', '/api/accounts/acc1/net_changes*', {
    statusCode: 200,
    body: { status: 'success', data: { income: 0, expense: 0, net: 0 } },
  }).as('net')

  cy.intercept('GET', '/api/transactions/acc1/transactions*', {
    statusCode: 200,
    body: { status: 'success', data: { transactions: [] } },
  }).as('tx')

  cy.intercept('GET', '/api/accounts/acc1/history?range=30d', (req) => {
    call += 1
    if (call === 1) {
      req.reply({ statusCode: 500, body: {} })
    } else {
      req.reply({
        statusCode: 200,
        body: { accountId: 'acc1', asOfDate: '2025-08-03', balances: [] },
      })
    }
  }).as('hist')

  cy.mount(Accounts, {
    global: {
      stubs: {
        LinkAccount: true,
        RefreshPlaidControls: true,
        RefreshTellerControls: true,
        TokenUpload: true,
        NetYearComparisonChart: true,
        AssetsBarTrended: true,
        AccountsReorderChart: true,
        InstitutionTable: true,
      },
    },
  })

  return cy.wait('@net').wait('@tx').wait('@hist')
}

describe('Accounts retry logic', () => {
  it('retries fetching history when requested', () => {
    mountWithFailingHistory()
    cy.contains('Failed to load history')
    cy.get('[data-testid="retry-button"]').click()
    cy.wait('@hist')
    cy.get('[data-testid="history-chart"]').should('exist')
  })
})
