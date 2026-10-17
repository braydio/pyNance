// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TransactionInsightsPanel from '../TransactionInsightsPanel.vue'

const insights = {
  matching_count: 2005,
  gross_spend: 540,
  refunds: 40,
  net_spend: 500,
  income: 3000,
  inflow: {
    economic_income: 3000,
    all_credit_movements: 3300,
    transfers_in: 200,
    unclassified_in: 100,
  },
  uncategorized_count: 4,
  recurring_candidate_count: 2,
  transfer_pair_count: 1,
  coverage: { unclassified_count: 1 },
  review_items: [
    {
      id: 'transfer_candidate:t2',
      kind: 'transfer_candidate',
      priority: 1,
      count: 1,
      amount_total: 100,
      transaction_ids: ['t2'],
      explanation: '1 transfer-looking transaction is not matched.',
      evidence: ['Provider labels it a transfer'],
      filter: { review: 'transfer_candidate' },
    },
    {
      id: 'possible_duplicate_same_merchant_amount_day:a',
      kind: 'possible_duplicate_same_merchant_amount_day',
      priority: 2,
      count: 2,
      amount_total: 36,
      transaction_ids: ['a', 'b'],
      explanation: 'Possible duplicate: 2 charges of 18.00 at Cafe on 2026-10-13.',
      evidence: ['Same account', 'Same merchant'],
      filter: { search: 'Cafe' },
    },
  ],
}

const mountPanel = (props = {}) =>
  mount(TransactionInsightsPanel, { props: { insights, scopeLabel: 'Last 30 days', ...props } })

describe('TransactionInsightsPanel', () => {
  it('shows the scope and server-side metrics, not a count of loaded rows', () => {
    const wrapper = mountPanel()
    expect(wrapper.get('[data-testid="insights-scope"]').text()).toBe('Last 30 days')
    expect(wrapper.get('[data-testid="metric-spending"]').text()).toContain('$500.00')
    expect(wrapper.get('[data-testid="metric-spending"]').text()).toContain(
      '$540.00 spent, $40.00 refunded',
    )
    expect(wrapper.get('[data-testid="metric-review"]').text()).toContain('3') // 1 + 2 items' transactions
    expect(wrapper.get('[data-testid="metric-recurring"]').text()).toContain('2')
    expect(wrapper.get('[data-testid="insights-matching"]').text()).toContain(
      '2,005 matching transactions',
    )
  })

  it('labels income as earned income and separates every other credit', () => {
    const text = mountPanel().get('[data-testid="metric-income"]').text()
    expect(text).toContain('$3,000.00')
    expect(text).toContain('Earned income only')
    expect(text).toContain('Other credits: $300.00')
    expect(text).toContain('transfers $200.00')
    expect(text).toContain('unreviewed $100.00')
  })

  it('lists review items with evidence and calls the item out when applied', async () => {
    const wrapper = mountPanel()
    const duplicate = wrapper.get(
      '[data-testid="review-possible_duplicate_same_merchant_amount_day"]',
    )
    expect(duplicate.text()).toContain('Possible duplicate')
    expect(duplicate.text()).toContain('Same account · Same merchant')
    await duplicate.get('button').trigger('click')
    expect(wrapper.emitted('apply')[0][0].kind).toBe('possible_duplicate_same_merchant_amount_day')
    const transfer = wrapper.get('[data-testid="review-transfer_candidate"]')
    expect(transfer.get('button').text()).toBe('Open Transfer Review')
    expect(transfer.get('button').attributes('aria-label')).toContain('not matched')
  })

  it('never mutates: applying only emits and buttons do not submit', async () => {
    const wrapper = mountPanel()
    wrapper.findAll('button').forEach((b) => expect(b.attributes('type')).toBe('button'))
  })

  it('refreshes on request and reports loading, errors and the empty state', async () => {
    const wrapper = mountPanel({ insights: { ...insights, review_items: [] } })
    expect(wrapper.get('[data-testid="review-empty"]').text()).toContain('Nothing needs review')
    await wrapper.get('[data-testid="insights-refresh"]').trigger('click')
    expect(wrapper.emitted('refresh')).toHaveLength(1)

    const loading = mountPanel({ insights: null, loading: true })
    expect(loading.text()).toContain('Loading summary')
    expect(loading.get('[data-testid="insights-refresh"]').attributes('disabled')).toBeDefined()

    const failed = mountPanel({ insights: null, error: 'Unable to load the summary.' })
    expect(failed.get('[role="alert"]').text()).toContain('Unable to load the summary.')
    await failed.get('[role="alert"] button').trigger('click')
    expect(failed.emitted('refresh')).toHaveLength(1)
  })
})
