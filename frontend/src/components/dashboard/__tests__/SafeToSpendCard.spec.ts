// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { config, mount } from '@vue/test-utils'
import SafeToSpendCard from '../SafeToSpendCard.vue'

config.global.stubs = { ...config.global.stubs, 'router-link': { template: '<a><slot /></a>' } }

const payload = {
  amount_cents: 4200,
  total_horizon_cents: 4200,
  per_day_cents: 4200,
  status: 'caution',
  mode: 'today',
  as_of: '2026-07-12',
  horizon_end: '2026-07-12',
  confidence: 'ready',
  message: 'You have about $42 today.',
  components: {
    spendable_cash_cents: 124000,
    upcoming_outflows_cents: 86000,
    required_buffer_cents: 25000,
    spent_today_cents: 8800,
  },
}

describe('SafeToSpendCard', () => {
  it('renders spend guidance and component math', () => {
    const wrapper = mount(SafeToSpendCard, {
      props: { payload, selectedMode: 'today' },
    })

    expect(wrapper.text()).toContain('Safe to Spend')
    expect(wrapper.text()).toContain('$42')
    expect(wrapper.text()).toContain('Spendable cash')
    expect(wrapper.text()).toContain('$1,240')
    expect(wrapper.text()).toContain('Confidence: ready')
  })

  it('shows the daily allowance, windows, payday source and buffer disclosure', () => {
    const full = {
      ...payload,
      amount_cents: 2307,
      total_protected_room_cents: 30000,
      default_buffer_cents: 25000,
      display_window: { start: '2026-10-17', end: '2026-10-17', days: 1 },
      protection_window: {
        start: '2026-10-17',
        end: '2026-10-29',
        days: 13,
        basis: 'day_before_payday',
      },
      payday_prediction: { next_payday: '2026-10-30', needs_review: true, confidence: 'medium' },
      warnings: ['Payday is inferred from past deposits, not confirmed.'],
    }
    const wrapper = mount(SafeToSpendCard, { props: { payload: full, selectedMode: 'today' } })
    expect(wrapper.text()).toContain('Daily allowance')
    expect(wrapper.get('[data-testid="protected-total"]').text()).toContain('$300')
    expect(wrapper.get('[data-testid="windows"]').text()).toContain(
      'Protecting 2026-10-17 to 2026-10-29',
    )
    expect(wrapper.get('[data-testid="windows"]').text()).toContain('(inferred, medium confidence)')
    expect(wrapper.text()).toContain('$250 default')
    expect(wrapper.get('[data-testid="warnings"]').text()).toContain('inferred')
    expect(wrapper.text()).toContain('Protected through 2026-10-29')
  })

  it('labels the rolling week honestly', () => {
    const wrapper = mount(SafeToSpendCard, { props: { payload, selectedMode: 'week' } })
    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toContain('Next 7 Days')
    expect(labels).not.toContain('This Week')
  })

  it('emits mode changes for next-version horizons', async () => {
    const wrapper = mount(SafeToSpendCard, {
      props: { payload, selectedMode: 'today' },
    })

    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:mode')?.[0]).toEqual(['until_payday'])
  })

  it('shows loading and error states', () => {
    const loading = mount(SafeToSpendCard, { props: { loading: true } })
    expect(loading.text()).toContain('Calculating spend room')

    const error = mount(SafeToSpendCard, { props: { error: 'Unavailable' } })
    expect(error.text()).toContain('Unavailable')
  })

  describe('reserved bills disclosure', () => {
    const rent = {
      id: 's1',
      name: 'Rent',
      account_id: 'chk',
      due_date: '2026-10-21',
      amount_cents: 70000,
      source: 'recurring_confirmed',
      status: 'confirmed',
      estimated: false,
      reason_codes: ['confirmed_stream', 'cadence_monthly'],
    }
    const withBills = {
      ...payload,
      mode: 'today',
      protection_window: {
        start: '2026-10-17',
        end: '2026-10-29',
        days: 13,
        basis: 'day_before_payday',
      },
      components: {
        ...payload.components,
        upcoming_outflows_cents: 70000,
        planned_bills_cents: 0,
        confirmed_recurring_cents: 70000,
        provisional_recurring_cents: 0,
        needs_review_cents: 0,
      },
      accounts: [{ account_id: 'chk', name: 'Everyday Checking' }],
      upcoming_bills: [rent],
      needs_review_bills: [],
      obligation_coverage: {
        complete: true,
        display_window_due_cents: 0,
        protection_window_reserved_cents: 70000,
      },
    }
    const mountCard = (props: Record<string, unknown>) => mount(SafeToSpendCard, { props })

    it('explains a future bill as protected, not due today, without raw ids', async () => {
      const wrapper = mountCard({ payload: withBills, selectedMode: 'today' })
      const toggle = wrapper.get('.safe-spend-card__reserved-toggle')
      expect(toggle.attributes('aria-expanded')).toBe('false')
      expect(wrapper.get('[data-testid="reserved-summary"]').text()).toBe(
        '$0 due today; $700 more is protected for bills due before 2026-10-29.',
      )
      await toggle.trigger('click')
      expect(toggle.attributes('aria-expanded')).toBe('true')
      const row = wrapper.get('[data-testid="bill-row"]').text()
      expect(row).toContain('Rent')
      expect(row).toContain('2026-10-21')
      expect(row).toContain('Everyday Checking')
      expect(row).toContain('-$700')
      expect(row).not.toContain('chk')
      expect(wrapper.get('[data-testid="reserved-panel"]').text()).toContain('Confirmed recurring')
      expect(wrapper.text()).toContain('Bills due after 2026-10-29 are not reserved yet.')
    })

    it('labels provisional and estimated rows honestly and keeps groups separate', async () => {
      const provisional = {
        ...rent,
        id: 's2',
        name: 'Gym',
        status: 'provisional',
        estimated: true,
        amount_cents: 4000,
      }
      const data = {
        ...withBills,
        components: {
          ...withBills.components,
          upcoming_outflows_cents: 74000,
          provisional_recurring_cents: 4000,
        },
        upcoming_bills: [rent, provisional],
      }
      const wrapper = mountCard({ payload: data, selectedMode: 'week' })
      await wrapper.get('.safe-spend-card__reserved-toggle').trigger('click')
      const titles = wrapper.findAll('.safe-spend-card__group-title').map((t) => t.text())
      expect(titles).toEqual(['Confirmed recurring-$700', 'Provisional recurring-$40'])
      expect(wrapper.findAll('[data-testid="bill-row"]')[1].text()).toContain('estimated')
    })

    it('shows needs-review bills outside the reserve with a review link', () => {
      const data = {
        ...withBills,
        components: {
          ...withBills.components,
          upcoming_outflows_cents: 0,
          needs_review_cents: 4000,
        },
        upcoming_bills: [],
        needs_review_bills: [
          {
            id: 's3',
            name: 'Gym',
            due_date: '2026-10-21',
            amount_cents: 4000,
            reason_codes: ['needs_review_insufficient_cycles'],
          },
        ],
      }
      const wrapper = mountCard({ payload: data, selectedMode: 'today' })
      expect(wrapper.get('[data-testid="needs-review"]').text()).toContain(
        'Needs review (not reserved): 1 bill, $40',
      )
      expect(wrapper.get('[data-testid="review-row"]').text()).toContain('seen fewer than 3 times')
      expect(wrapper.text()).toContain('Review recurring bills')
    })

    it('never claims there are no bills when coverage is incomplete', async () => {
      const data = {
        ...withBills,
        components: {
          ...withBills.components,
          upcoming_outflows_cents: 0,
          confirmed_recurring_cents: 0,
        },
        upcoming_bills: [],
        obligation_coverage: { complete: false, display_window_due_cents: 0 },
        warnings: ['No posted cash transactions yet, so recurring bills cannot be detected.'],
      }
      const wrapper = mountCard({ payload: data, selectedMode: 'today' })
      expect(wrapper.get('[data-testid="reserved-summary"]').text()).toContain(
        'bill coverage is incomplete',
      )
      expect(wrapper.get('[data-testid="warnings"]').text()).toContain('cannot be detected')
      const clean = mountCard({
        payload: { ...data, obligation_coverage: { complete: true } },
        selectedMode: 'today',
      })
      expect(clean.get('[data-testid="reserved-summary"]').text()).toBe(
        'No known bills are reserved through 2026-10-29.',
      )
    })
  })
})
