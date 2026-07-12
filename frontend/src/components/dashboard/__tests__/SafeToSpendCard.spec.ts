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
