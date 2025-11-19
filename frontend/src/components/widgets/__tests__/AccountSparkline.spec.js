// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import AccountSparkline from '../AccountSparkline.vue'

const balanceHistory = ref([
  { balance: 100 },
  { balance: 150 },
  { balance: 90 },
])

const transactionHistory = ref([
  { net_amount: 20 },
  { net_amount: -10 },
  { net_amount: 35 },
])

vi.mock('@/composables/useAccountHistory', () => ({
  useAccountHistory: () => ({
    history: balanceHistory,
    balances: balanceHistory,
    loading: ref(false),
    loadHistory: vi.fn(),
  }),
}))

vi.mock('@/composables/useAccountTransactionHistory', () => ({
  useAccountTransactionHistory: () => ({
    history: transactionHistory,
    loading: ref(false),
    fetchHistory: vi.fn(),
  }),
}))

describe('AccountSparkline accessibility', () => {
  beforeEach(() => {
    balanceHistory.value = [
      { balance: 100 },
      { balance: 150 },
      { balance: 90 },
    ]
    transactionHistory.value = [
      { net_amount: 20 },
      { net_amount: -10 },
      { net_amount: 35 },
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
    expect(toggle.text()).toContain('Balance history sparkline selected. Activate to view transactions.')

    const indicatorHint = wrapper.get('.sparkline-indicator .sr-only')
    expect(indicatorHint.text()).toBe('Indicator letter B represents balance history.')
  })

  it('supports keyboard and pointer activation while updating aria-pressed state', async () => {
    const wrapper = mount(AccountSparkline, {
      props: {
        accountId: 'acct-456',
      },
    })

    const toggle = wrapper.get('button.sparkline-container')

    await toggle.trigger('keydown.enter')
    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(wrapper.get('.sparkline-indicator .sr-only').text()).toBe(
      'Indicator letter T represents transaction history.',
    )

    toggle.element.dispatchEvent(new MouseEvent('click', { bubbles: true, detail: 0 }))
    await wrapper.vm.$nextTick()
    expect(toggle.attributes('aria-pressed')).toBe('true')

    toggle.element.dispatchEvent(new MouseEvent('click', { bubbles: true, detail: 1 }))
    await wrapper.vm.$nextTick()
    expect(toggle.attributes('aria-pressed')).toBe('false')
  })
})
