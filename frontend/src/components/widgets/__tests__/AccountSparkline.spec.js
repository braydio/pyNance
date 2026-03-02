// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import AccountSparkline from '../AccountSparkline.vue'

const normalizedHistory = ref([
  { date: '2024-01-01', balance: 100 },
  { date: '2024-01-02', balance: 150 },
  { date: '2024-01-03', balance: 90 },
])

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: () => ({
    history: normalizedHistory,
    balances: normalizedHistory,
    loading: ref(false),
    error: ref(null),
    isReady: ref(true),
    loadHistory: vi.fn(),
  }),
}))

describe('AccountSparkline accessibility', () => {
  beforeEach(() => {
    normalizedHistory.value = [
      { date: '2024-01-01', balance: 100 },
      { date: '2024-01-02', balance: 150 },
      { date: '2024-01-03', balance: 90 },
    ]
  })

  it('renders toggle button with descriptive content for the indicator', () => {
    const wrapper = mount(AccountSparkline, {
      props: {
        accountId: 'acct-123',
      },
    })

    const toggle = wrapper.get('button.sparkline-container')
    expect(toggle.attributes('aria-pressed')).toBe('false')
    expect(toggle.text()).toContain(
      'Balance history sparkline selected. Activate to view transactions.',
    )

    const indicatorHint = wrapper.get('.sparkline-indicator .sr-only')
    expect(indicatorHint.text()).toBe('Indicator letter B represents balance history.')
  })

  it('uses the same normalized history dataset for balance and transactions modes', async () => {
    const wrapper = mount(AccountSparkline, {
      props: {
        accountId: 'acct-456',
      },
    })

    const toggle = wrapper.get('button.sparkline-container')
    const balancePoints = wrapper.get('polyline').attributes('points')

    await toggle.trigger('keydown.enter')

    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(wrapper.get('.sparkline-indicator .sr-only').text()).toBe(
      'Indicator letter T represents transaction history.',
    )
    expect(wrapper.get('polyline').attributes('points')).toBe(balancePoints)
  })
})
