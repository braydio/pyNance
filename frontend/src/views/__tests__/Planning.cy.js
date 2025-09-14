/**
 * Cypress tests for planning state operations: bill add/edit/delete,
 * allocation total calculations, and summary summaries.
 */
import {
  selectAllocatedCents,
  selectRemainingCents,
  selectTotalBillsCents,
} from '@/selectors/planning'

// Generate a baseline planning state
function makeState() {
  return {
    version: 1,
    devMode: false,
    bills: [],
    scenarios: [],
    activeScenarioId: '',
    activeScenarioIdByAccount: {},
    lastSavedAt: '',
  }
}

describe('planning selectors', () => {
  it('handles bill add, edit, and delete', () => {
    const state = makeState()
    const bill = {
      id: 'b1',
      name: 'Rent',
      amountCents: 50000,
      dueDate: '2024-01-01',
      origin: 'manual',
      accountId: '',
    }

    // add
    state.bills.push(bill)
    expect(selectTotalBillsCents(state)).to.eq(50000)

    // edit
    state.bills = state.bills.map((b) =>
      b.id === bill.id ? { ...b, amountCents: 60000 } : b
    )
    expect(selectTotalBillsCents(state)).to.eq(60000)

    // delete
    state.bills = state.bills.filter((b) => b.id !== bill.id)
    expect(selectTotalBillsCents(state)).to.eq(0)
  })

  it('computes allocation totals and remaining cents', () => {
    const scenario = {
      id: 's1',
      name: 'Base',
      planningBalanceCents: 100000,
      allocations: [
        { id: 'a1', target: 'savings:emergency', kind: 'fixed', value: 20000 },
        { id: 'a2', target: 'goal:vacation', kind: 'percent', value: 10 },
      ],
      accountId: '',
    }

    const allocated = selectAllocatedCents(scenario)
    expect(allocated).to.eq(20000 + Math.floor((100000 * 10) / 100))

    const remaining = selectRemainingCents(scenario)
    expect(remaining).to.eq(100000 - allocated)
  })

  it('summarizes totals from state and scenario', () => {
    const state = makeState()
    state.bills = [
      {
        id: 'b1',
        name: 'Rent',
        amountCents: 50000,
        dueDate: '2024-01-01',
        origin: 'manual',
        accountId: '',
      },
      {
        id: 'b2',
        name: 'Utilities',
        amountCents: 10000,
        dueDate: '2024-01-05',
        origin: 'manual',
        accountId: '',
      },
    ]

    state.scenarios = [
      {
        id: 's1',
        name: 'Base',
        planningBalanceCents: 100000,
        allocations: [
          { id: 'a1', target: 'savings:emergency', kind: 'fixed', value: 20000 },
        ],
        accountId: '',
      },
    ]

    state.activeScenarioId = 's1'
    const scenario = state.scenarios[0]

    expect(selectTotalBillsCents(state)).to.eq(60000)
    expect(selectAllocatedCents(scenario)).to.eq(20000)
    expect(selectRemainingCents(scenario)).to.eq(80000)
  })
})
