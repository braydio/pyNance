import Accounts from '../Accounts.vue'

function mountWithData() {
  cy.intercept('GET', '/api/accounts/get_accounts', {
    statusCode: 200,
    body: { status: 'success', accounts: [{ account_id: 'acc1' }] },
  }).as('getAccounts')

  cy.intercept('GET', '/api/accounts/acc1/net_changes', {
    statusCode: 200,
    body: { status: 'success', data: { income: 100, expense: 50, net: 50 } },
  }).as('getSummary')

  cy.intercept('GET', '/api/transactions/acc1/transactions*', {
    statusCode: 200,
    body: {
      status: 'success',
      data: {
        transactions: [
          {
            transaction_id: 'tx1',
            date: '2024-01-01',
            amount: -50,
            description: 'Test',
            category: 'misc',
            institution_name: 'Bank',
            account_name: 'Checking',
            merchant_name: 'Store',
            subtype: 'checking',
          },
        ],
        total: 1,
      },
    },
  }).as('getTx')

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

  cy.wait(['@getAccounts', '@getSummary', '@getTx'])
}

describe('Accounts summary view', () => {
  it('shows summary and transactions', () => {
    mountWithData()
    cy.contains('Net Change Summary').should('exist')
    cy.contains('Income').should('exist')
    cy.contains('Recent Transactions').should('exist')
    cy.get('table').should('exist')
  })
})
