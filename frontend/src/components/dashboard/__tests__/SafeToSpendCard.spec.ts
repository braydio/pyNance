// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SafeToSpendCard from '../SafeToSpendCard.vue'

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
      protection_window: { start: '2026-10-17', end: '2026-10-29', days: 13, basis: 'day_before_payday' },
      payday_prediction: { next_payday: '2026-10-30', needs_review: true, confidence: 'medium' },
      warnings: ['Payday is inferred from past deposits, not confirmed.'],
    }
    const wrapper = mount(SafeToSpendCard, { props: { payload: full, selectedMode: 'today' } })
    expect(wrapper.text()).toContain('Daily allowance')
    expect(wrapper.get('[data-testid="protected-total"]').text()).toContain('$300')
    expect(wrapper.get('[data-testid="windows"]').text()).toContain('Protecting 2026-10-17 to 2026-10-29')
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
})
