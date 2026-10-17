// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ForecastSummaryPanel from '../ForecastSummaryPanel.vue'

const baseProps = {
  assetBalance: 900,
  liabilityBalance: 500,
  netBalance: 400,
  manualIncome: 120,
  liabilityRate: 40,
  viewType: 'Month',
  includedAccountIds: ['acc-1'],
  excludedAccountIds: [],
  accountOptions: [
    { account_id: 'acc-1', name: 'Checking', institution_name: 'Bank A' },
    { account_id: 'acc-2', name: 'Savings', institution_name: 'Bank B' },
  ],
  computeMeta: {
    lookbackDays: 90,
    movingAverageWindow: 30,
    normalize: false,
    includesAutoDetectedAdjustments: true,
    autoDetectedAdjustmentCount: 2,
  },
}

describe('ForecastSummaryPanel', () => {
  it('emits include/exclude account updates when toggles are clicked', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: baseProps,
    })

    await wrapper.get('.value-link').trigger('click')
    const excludeChips = wrapper.findAll('.selector-item .chip-exclude')
    await excludeChips[1].trigger('click')

    const includedEvents = wrapper.emitted('update:includedAccountIds')
    const excludedEvents = wrapper.emitted('update:excludedAccountIds')

    expect(includedEvents).toBeTruthy()
    expect(excludedEvents).toBeTruthy()
    expect(includedEvents?.at(-1)?.[0]).toEqual(['acc-1'])
    expect(excludedEvents?.at(-1)?.[0]).toEqual(['acc-2'])
  })

  it('applies dashboard group shortcut as include selection', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...baseProps,
        includedAccountIds: [],
        excludedAccountIds: ['acc-2'],
        accountGroupOptions: [
          { id: 'group-1', name: 'Core accounts', accountIds: ['acc-1', 'acc-2'] },
        ],
      },
    })

    await wrapper.get('.selector-toggle').trigger('click')
    await wrapper.get('.shortcut-chip').trigger('click')

    expect(wrapper.emitted('update:includedAccountIds')?.at(-1)?.[0]).toEqual(['acc-1', 'acc-2'])
    expect(wrapper.emitted('update:excludedAccountIds')?.at(-1)?.[0]).toEqual([])
  })

  it('renders asset, liability, and current balance values with tooltip copy', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...baseProps,
        assetBalance: 2500,
        liabilityBalance: 800,
        netBalance: 1700,
      },
    })

    expect(wrapper.text()).toContain('Assets')
    expect(wrapper.text()).toContain('$2,500.00')
    expect(wrapper.text()).toContain('Liabilities')
    expect(wrapper.text()).toContain('$800.00')
    expect(wrapper.text()).toContain('Current Balance')
    expect(wrapper.text()).toContain('$1,700.00')
    expect(wrapper.text()).toContain('positive-balance accounts currently included in the forecast')
    expect(wrapper.text()).toContain('Current Balance is assets minus liabilities')
  })

  it('prefers computed forecast net change when provided and explains the calculation inputs', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...baseProps,
        netChange: 123.45,
      },
    })

    expect(wrapper.text()).toContain('Net Delta:')
    expect(wrapper.text()).toContain('+$123.45')
    expect(wrapper.text()).toContain('30-day moving average')
    expect(wrapper.text()).toContain('latest 90 days of history')
    expect(wrapper.text()).toContain('includes 2 auto-detected adjustments')
  })

  it('updates manual input tooltip copy when the controls change', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: baseProps,
    })

    expect(wrapper.text()).toContain('Manual Income adds $120.00 per day')
    expect(wrapper.text()).toContain('Liability Rate subtracts $40.00 per day')

    await wrapper.setProps({
      manualIncome: 225,
      liabilityRate: 65,
      viewType: 'Year',
    })

    expect(wrapper.text()).toContain(
      'Manual Income adds $225.00 per day to the projection in Year view',
    )
    expect(wrapper.text()).toContain(
      'Liability Rate subtracts $65.00 per day from the projection in Year view',
    )
  })

  it('keeps manual baseline inputs in a collapsed disclosure and leads with net change', () => {
    const wrapper = mount(ForecastSummaryPanel, { props: { netChange: 42 } })
    expect(wrapper.get('[data-testid="manual-inputs"]').attributes('open')).toBeUndefined()
    expect(wrapper.find('#manual-income-input').exists()).toBe(true)
    expect(wrapper.get('[data-testid="summary-lead"]').text()).toContain('Net change')
  })

  it('labels the manual inputs with their dollars-per-day units and explains they apply live', () => {
    const wrapper = mount(ForecastSummaryPanel, { props: baseProps })
    const income = wrapper.get('label[for="manual-income-input"]').text()
    const rate = wrapper.get('label[for="liability-rate-input"]').text()
    expect(income).toContain('$ per day')
    expect(rate).toContain('$ per day')
    const note = wrapper.get('#manual-inputs-note')
    expect(note.text()).toContain('dollars per day')
    expect(note.text()).toContain('apply to the forecast as you type')
    expect(wrapper.get('#manual-income-input').attributes('aria-describedby')).toBe(
      'manual-inputs-note',
    )
    expect(wrapper.get('#liability-rate-input').attributes('aria-describedby')).toBe(
      'manual-inputs-note',
    )
  })

  describe('debt coverage wording', () => {
    const liquidity = {
      starting_cash: 5000,
      ending_cash: 3200.5,
      min_cash: 1200,
      min_cash_date: '2026-11-20',
      first_shortfall_date: null,
    }
    const netWorth = {
      starting: 9300,
      ending: 9000,
      liabilities: { starting: 11686.65, ending: 11186.65 },
      investments: { starting: 5000, ending: 5000 },
    }
    const v2 = (debtPaymentCoverage: Record<string, unknown> | null) =>
      mount(ForecastSummaryPanel, {
        props: { ...baseProps, modelVersion: 'v2', liquidity, netWorth, debtPaymentCoverage },
      })
    const payment = (id: string, date: string, amount: string) => ({
      stream_id: id,
      date,
      amount,
      source: 'recurring',
    })

    it('separates outstanding debt from scheduled payments and says what is verified', () => {
      const wrapper = v2({
        mode: 'mixed',
        included: [payment('s1', '2026-11-15', '500.00'), payment('s1', '2026-12-15', '500.00')],
        settled_account_ids: ['card'],
        unmodeled_account_count: 1,
        unknown_payment_account_ids: ['loan'],
        invalid_payment_stream_ids: [],
      })
      expect(wrapper.get('[data-testid="debt-outstanding"]').text()).toContain(
        'Outstanding debt tracked separately: $11,686.65',
      )
      expect(wrapper.get('[data-testid="debt-outstanding"]').text()).toContain('not a cash event')
      expect(wrapper.get('[data-testid="debt-payments-included"]').text()).toBe(
        'Scheduled debt payments included: $1,000.00 across 1 verified stream.',
      )
      expect(wrapper.get('[data-testid="debt-coverage-status"]').text()).toContain(
        'Other debt payment coverage: incomplete. 1 account has no verified payment plan',
      )
      expect(wrapper.text()).not.toContain('Not part of this cash forecast: debt')
    })

    it('reports complete coverage and counts distinct streams', () => {
      const wrapper = v2({
        mode: 'settlement',
        included: [payment('a', '2026-11-15', '300.00'), payment('b', '2026-11-20', '220.50')],
        settled_account_ids: ['card', 'loan'],
        unmodeled_account_count: 0,
        unknown_payment_account_ids: [],
        invalid_payment_stream_ids: [],
      })
      expect(wrapper.get('[data-testid="debt-payments-included"]').text()).toContain(
        '$520.50 across 2 verified streams',
      )
      expect(wrapper.get('[data-testid="debt-coverage-status"]').text()).toContain(
        'every tracked card and loan has a verified payment plan',
      )
    })

    it('does not pretend payments are covered when there is no verified plan or no data', () => {
      const none = v2({
        mode: 'proxy',
        included: [],
        settled_account_ids: [],
        unmodeled_account_count: 2,
        unknown_payment_account_ids: ['card', 'loan'],
        invalid_payment_stream_ids: [],
      })
      expect(none.get('[data-testid="debt-payments-included"]').text()).toContain('none')
      expect(none.get('[data-testid="debt-coverage-status"]').text()).toContain('unverified')
      expect(none.get('[data-testid="debt-coverage-status"]').classes()).toContain(
        'debt-coverage__caution',
      )
      expect(v2(null).get('[data-testid="debt-coverage-status"]').text()).toBe(
        'Other debt payment coverage: unverified.',
      )
    })

    it('keeps V1 copy honest and formats V1 values with helpers', () => {
      const wrapper = mount(ForecastSummaryPanel, {
        props: {
          ...baseProps,
          assetBalance: 12345.6,
          liabilityBalance: 11686.65,
          netBalance: 658.95,
        },
      })
      expect(wrapper.get('[data-testid="v1-debt-note"]').text()).toBe(
        'Debt totals are separate from modeled bank cash.',
      )
      expect(wrapper.text()).toContain('$12,345.60')
      expect(wrapper.text()).toContain('$11,686.65')
      expect(wrapper.text()).not.toMatch(/\.\d{3,}/) // no raw toFixed/float tails
    })

    it('shows a negative net change with a true minus and a zero net as $0.00', () => {
      const negative = mount(ForecastSummaryPanel, { props: { ...baseProps, netChange: -25.4 } })
      expect(negative.get('[data-testid="summary-lead"]').text()).toContain('\u2212$25.40')
      const zero = mount(ForecastSummaryPanel, { props: { ...baseProps, netChange: 0 } })
      expect(zero.get('[data-testid="summary-lead"]').text()).toContain('$0.00')
    })
  })
})
