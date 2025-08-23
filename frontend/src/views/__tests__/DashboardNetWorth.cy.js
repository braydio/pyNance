// DashboardNetWorth.cy.js
// Ensures Dashboard displays appropriate net worth message based on balance.
import Dashboard from '../Dashboard.vue'

const NEGATIVE_MESSAGES = [
  "Yikes! You're in the red.",
  'Looks like debts outweigh assets.'
]
const POSITIVE_MESSAGES = [
  'Awesome! Your fortune grows.',
  "You're well in the black."
]
const NEUTRAL_MESSAGES = ['Steady as she goes.', 'Room for growth ahead.']

function mountWithWorth(value) {
  cy.intercept('GET', '/api/charts/net_assets', {
    statusCode: 200,
    body: { status: 'success', data: [{ date: '2024-01-01', net_assets: value }] },
  }).as('getNetAssets')

  cy.mount(Dashboard, {
    global: {
      stubs: {
        AppLayout: true,
        BaseCard: true,
        PaginationControls: true,
        DailyNetChart: true,
        CategoryBreakdownChart: true,
        AccountsTable: true,
        TransactionsTable: true,
        TransactionModal: true,
        AccountSnapshot: true,
        FinancialSummary: true,
      },
    },
  })
  return cy.wait('@getNetAssets')
}

describe('Dashboard net worth message', () => {
  it('uses negative balance pool', () => {
    mountWithWorth(-500)
    cy.get('p.italic').invoke('text').should(text => {
      expect(NEGATIVE_MESSAGES).to.include(text.trim())
    })
  })

  it('uses positive balance pool', () => {
    mountWithWorth(1500)
    cy.get('p.italic').invoke('text').should(text => {
      expect(POSITIVE_MESSAGES).to.include(text.trim())
    })
  })

  it('uses neutral balance pool', () => {
    mountWithWorth(500)
    cy.get('p.italic').invoke('text').should(text => {
      expect(NEUTRAL_MESSAGES).to.include(text.trim())
    })
  })
})
