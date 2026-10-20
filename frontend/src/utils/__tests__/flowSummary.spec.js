import { describe, expect, it } from 'vitest'
import {
  disagreesWithChart,
  flowChipLabel,
  flowTitle,
  summarizeFlows,
  visiblePageSubtotal,
} from '../flowSummary'

const row = (id, kind, delta, extra = {}) => ({
  transaction_id: id,
  date: '2026-10-13',
  amount: delta,
  signed_account_delta: delta,
  reporting_flow_kind: kind,
  economic_amount: ['income', 'expense', 'refund'].includes(kind) ? delta : null,
  flow_reason_codes: [],
  ...extra,
})

// Oct 13 fixture: two credits that are not wages must not become income.
const OCT_13 = [
  row('zelle', 'transfer', 200, {
    flow_reason_codes: ['confirmed_internal'],
    flow_confidence: 'high',
  }),
  row('brokerage', 'unclassified', 100, { flow_reason_codes: ['pfc_account_transfer_unpaired'] }),
  row('loan', 'debt_settlement', -131.64),
  row('adobe-1', 'expense', -12.89),
  row('adobe-2', 'expense', -21.49),
  row('interest', 'expense', -265.71),
]

describe('summarizeFlows', () => {
  it('keeps transfers and unresolved credits out of income and net', () => {
    const s = summarizeFlows(OCT_13)
    expect(s.classified).toBe(true)
    expect(s.income).toBe(0)
    expect(s.expense).toBe(-300.09)
    expect(s.net).toBe(-300.09)
    expect(s.transfersIn).toBe(200)
    expect(s.transferCount).toBe(1)
    expect(s.debtPayments).toBe(131.64)
    expect(s.unclassifiedCount).toBe(1)
    expect(s.unclassifiedAmount).toBe(100)
  })

  it('counts payroll as income, a refund as a refund, and every row exactly once', () => {
    const s = summarizeFlows([row('pay', 'income', 1000), row('refund', 'refund', 25), ...OCT_13])
    expect(s.income).toBe(1000)
    expect(s.refunds).toBe(25)
    expect(s.net).toBe(724.91)
    expect(s.counted).toBe(8)
  })

  it('treats rows without a classification as needing review, never as income', () => {
    const s = summarizeFlows([row('a', 'income', 5), { transaction_id: 'b', amount: 50 }])
    expect(s.income).toBe(5)
    expect(s.unclassifiedCount).toBe(1)
    expect(summarizeFlows([{ transaction_id: 'c', amount: 9 }]).classified).toBe(false)
  })

  it('excludes pending rows from totals but counts them', () => {
    const s = summarizeFlows([row('p', 'expense', -10, { pending: true }), row('q', 'expense', -5)])
    expect(s.expense).toBe(-5)
    expect(s.pendingCount).toBe(1)
  })

  it('handles empty input', () => {
    expect(summarizeFlows([])).toMatchObject({ classified: false, net: 0, counted: 0 })
    expect(summarizeFlows(null).net).toBe(0)
  })
})

describe('chart reconciliation and labels', () => {
  it('flags only a real disagreement with the chart bucket', () => {
    const s = summarizeFlows(OCT_13)
    expect(disagreesWithChart(s, { income: 0, expenses: -300.09, net: -300.09 })).toBe(false)
    expect(disagreesWithChart(s, { income: 0, expenses: -250, net: -250 })).toBe(true)
    expect(disagreesWithChart(s, null)).toBe(false)
  })

  it('labels non-economic rows and explains them without claiming verification', () => {
    expect(flowChipLabel(row('t', 'transfer', 1))).toBe('Transfer')
    expect(flowChipLabel(row('u', 'unclassified', 1))).toBe('Review')
    expect(flowChipLabel(row('e', 'expense', -1))).toBe('')
    expect(flowChipLabel({ amount: 1 })).toBe('')
    const title = flowTitle(OCT_13[1])
    expect(title).toContain('no matching pair')
    expect(title).not.toMatch(/verified/i)
  })
})

describe('visiblePageSubtotal', () => {
  it('sums only the rendered rows and keeps cash movement apart from economic amounts', () => {
    const rows = [
      { amount: -10.1, economic_amount: -10.1 },
      { amount: -0.2, economic_amount: -0.2 },
      { amount: 200, economic_amount: null }, // transfer: cash moved, nothing economic
      { _placeholder: true, amount: 999, economic_amount: 999 },
      { amount: 'n/a' },
    ]
    expect(visiblePageSubtotal(rows)).toEqual({ count: 4, cashMovement: 189.7, economic: -10.3 })
  })

  it('treats a missing page as empty rather than inventing zeros for failures', () => {
    expect(visiblePageSubtotal(undefined)).toEqual({ count: 0, cashMovement: 0, economic: 0 })
    expect(visiblePageSubtotal([])).toEqual({ count: 0, cashMovement: 0, economic: 0 })
  })
})
