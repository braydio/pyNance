// forecast-v2.cy.js - Forecast page with the V2 liquid-cash response mocked.
// Requires the app to be served with VITE_USER_ID_PLAID set (any non-empty value).

function v2Response(extra = {}) {
  const days = Array.from({ length: 30 }, (_, i) => {
    const day = new Date(Date.UTC(2026, 10, 1 + i)).toISOString().slice(0, 10)
    const cash = 5000 - i * 40
    return {
      date: day,
      label: day,
      forecast_balance: cash,
      liquid_cash: cash,
      actual_balance: null,
      p10: cash - 150 - i * 6,
      p50: cash - 10,
      p90: cash + 150 + i * 6,
    }
  })
  return {
    model_version: 'v2',
    status: 'ok',
    timeline: days,
    summary: {
      start_date: '2026-11-01',
      end_date: '2026-11-30',
      starting_balance: 5000,
      ending_balance: 3840,
      net_change: -1160,
      total_inflows: 2000,
      total_outflows: 3160,
      average_daily_change: -38.67,
      min_balance: 3840,
      max_balance: 5000,
      depletion_date: null,
      currency: 'USD',
      breakdowns: {},
      account_count: 2,
      recurring_count: 2,
    },
    cashflows: [],
    adjustments: [],
    series: {},
    metadata: { balance_basis: 'liquid_cash' },
    liquidity: {
      starting_cash: 5000,
      ending_cash: 3840,
      min_cash: 3840,
      min_cash_date: '2026-11-30',
      first_shortfall_date: null,
    },
    net_worth: {
      starting: 9300,
      ending: 8140,
      liabilities: { starting: 700, ending: 700 },
      investments: { starting: 5000, ending: 5000 },
    },
    uncertainty: {
      available: true,
      risk_below_zero_any_day: 0.02,
      risk_below_threshold_any_day: 0.21,
      threshold: 500,
      sample_count: 300,
      seed: 12345,
    },
    drivers: [
      {
        event_id: 'rent-1',
        source_id: 's-rent',
        date: '2026-11-01',
        amount: -1500,
        kind: 'scheduled_bill',
        origin: 'detected_recurring',
        confidence_label: 'high',
        label: 'landlord properties',
      },
    ],
    data_quality: { as_of_date: '2026-10-31', history_days: 120, confidence: 'high', warnings: [] },
    scenarios: [],
    ...extra,
  }
}

describe('Forecast page (V2)', () => {
  beforeEach(() => {
    cy.intercept('GET', '**/accounts/get_accounts*', {
      status: 'success',
      accounts: [{ account_id: 'chk', name: 'Checking', institution_name: 'Bank' }],
    })
    cy.intercept('GET', '**/groups*', { status: 'success', data: [] })
    cy.on('uncaught:exception', () => false)
  })

  it('leads with liquid cash outcomes, keeps debt separate and draws the range chart', () => {
    cy.intercept('POST', '/api/forecast/compute', (req) => {
      expect(req.body.model_version).to.eq('v2')
      req.reply(v2Response())
    }).as('compute')
    cy.visit('/forecast')
    cy.wait('@compute')

    cy.get('[data-testid="liquidity-summary"]').should('be.visible')
    cy.get('[data-testid="cash-today"]').should('contain', '$5,000.00')
    cy.get('[data-testid="shortfall"]').should('contain', 'No shortfall projected')
    cy.get('[data-testid="risk-copy"]').should('contain', '21%')
    cy.get('[data-testid="net-worth-note"]').should('contain', 'debt $700.00')
    cy.get('canvas').should('exist')
    cy.contains('What drives this forecast').click()
    cy.get('.driver-row')
      .should('contain', 'landlord properties')
      .and('contain', 'Detected pattern')
  })

  it('requests a scenario with a keyboard-operable control and shows replayed deltas', () => {
    cy.intercept('POST', '/api/forecast/compute', (req) => {
      const wanted = req.body.scenarios || []
      req.reply(
        wanted.length
          ? v2Response({
              scenarios: [
                {
                  id: 'baseline',
                  label: 'Baseline',
                  ending_cash: 3840,
                  min_cash: 3840,
                  min_cash_date: '2026-11-30',
                  first_shortfall_date: null,
                  delta_vs_baseline: { ending_cash: 0, min_cash: 0 },
                  timeline: [],
                  risk: null,
                },
                {
                  id: 'pay-delay',
                  label: 'Paycheck 7 days late',
                  ending_cash: 1840,
                  min_cash: 900,
                  min_cash_date: '2026-11-20',
                  first_shortfall_date: null,
                  delta_vs_baseline: { ending_cash: -2000, min_cash: -2940 },
                  timeline: [{ date: '2026-11-01', liquid_cash: 5000 }],
                  risk: null,
                },
              ],
            })
          : v2Response(),
      )
    }).as('compute')
    cy.visit('/forecast')
    cy.wait('@compute')

    cy.get('[data-testid="scenario-comparison"] input[type="checkbox"]').first().focus().type(' ')
    cy.get('@compute.all').should((calls) => {
      expect(
        calls.some((call) =>
          (call.request.body.scenarios || []).some((scenario) => scenario.id === 'pay-delay'),
        ),
      ).to.eq(true)
    })
    cy.get('[data-testid="scenario-row-pay-delay"]')
      .should('contain', '-$2,000.00')
      .and('contain', 'Paycheck 7 days late')
  })

  it('shows the server error instead of a blank page when scope is rejected', () => {
    cy.intercept('POST', '/api/forecast/compute', {
      statusCode: 403,
      body: { error: 'One or more requested accounts are not available to this user.' },
    })
    cy.visit('/forecast')
    cy.contains('not available to this user').should('be.visible')
  })

  it('does not overflow horizontally at phone width', () => {
    cy.intercept('POST', '/api/forecast/compute', v2Response())
    cy.viewport(360, 800)
    cy.visit('/forecast')
    cy.get('[data-testid="liquidity-summary"]').should('be.visible')
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(360)
    })
  })
})
