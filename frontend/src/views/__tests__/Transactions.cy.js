import Transactions from '../Transactions.vue'

function mountPage() {
  cy.intercept('GET', '/api/transactions/get_transactions*', {
    statusCode: 200,
    body: { transactions: [], total: 0 },
  }).as('tx')

  cy.mount(Transactions, {
    global: {
      stubs: {
        AccountActionsSidebar: true,
        UpdateTransactionsTable: true,
        RecurringTransactionSection: true,
        InternalTransferScanner: true,
      },
    },
  })

  return cy.wait('@tx')
}

describe('Transactions tabs', () => {
  it('navigates between tabs', () => {
    mountPage()
    cy.get('updatetransactionstable-stub').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Recurring').click()
    cy.get('recurringtransactionsection-stub').should('exist')
    cy.get('[data-testid="tabbed-nav"]').contains('Scanner').click()
    cy.get('internaltransferscanner-stub').should('exist')
  })
})
