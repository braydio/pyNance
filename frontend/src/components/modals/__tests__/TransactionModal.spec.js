// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import TransactionModal from '../TransactionModal.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

describe('TransactionModal.vue', () => {
  it('shows the date column for date drill-downs when requested', () => {
    const wrapper = shallowMount(TransactionModal, {
      props: {
        show: true,
        kind: 'date',
        showDateColumn: true,
        transactions: [{ transaction_id: 'tx-1', date: '2026-07-16', amount: -10 }],
      },
      global: {
        stubs: {
          transition: false,
          ModalTransactionsDisplay: {
            name: 'ModalTransactionsDisplay',
            props: ['showDateColumn'],
            template: '<div class="transactions-display" />',
          },
        },
      },
    })

    expect(wrapper.getComponent({ name: 'ModalTransactionsDisplay' }).props('showDateColumn')).toBe(
      true,
    )
  })
})

describe('TransactionModal.vue economic summary', () => {
  const tx = (id, kind, delta, extra = {}) => ({
    transaction_id: id,
    date: '2026-10-13',
    amount: delta,
    signed_account_delta: delta,
    reporting_flow_kind: kind,
    economic_amount: ['income', 'expense', 'refund'].includes(kind) ? delta : null,
    ...extra,
  })
  const mountModal = (props) =>
    shallowMount(TransactionModal, {
      props: { show: true, kind: 'date', ...props },
      global: { stubs: { transition: false, ModalTransactionsDisplay: true } },
    })

  it('reports $0 income for an own-account transfer and an unresolved credit, and lists them apart', () => {
    const wrapper = mountModal({
      transactions: [
        tx('zelle', 'transfer', 200),
        tx('brokerage', 'unclassified', 100),
        tx('adobe', 'expense', -12.89),
      ],
    })
    const text = wrapper.text()
    expect(text).toMatch(/Income\s*\(excl\. transfers\)\s*\$0\.00/)
    expect(text).toContain('Transfers in $200.00')
    expect(text).toContain('Needs classification: 1')
    expect(wrapper.get('[data-testid="movement-summary"]').text()).toContain('not in Net')
  })

  it('keeps the legacy sign split for feeds without a classification', () => {
    const wrapper = mountModal({
      kind: 'category',
      transactions: [
        { transaction_id: 'a', amount: -20 },
        { transaction_id: 'b', amount: 5 },
      ],
    })
    expect(wrapper.text()).toContain('$5.00')
    expect(wrapper.find('[data-testid="movement-summary"]').exists()).toBe(false)
  })

  it('shows partial-day and chart-disagreement notices', () => {
    const wrapper = mountModal({
      transactions: [tx('adobe', 'expense', -12.89)],
      notice: 'Partial activity: showing 1 of 1001 transactions',
      reference: { income: 0, expenses: -50, net: -50 },
    })
    const notes = wrapper.get('[data-testid="movement-summary"]').text()
    expect(notes).toContain('Partial activity')
    expect(notes).toContain('differ from the chart')
  })
})
