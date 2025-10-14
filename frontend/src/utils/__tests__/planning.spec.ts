import { describe, expect, it } from 'vitest'
import type { Allocation, Bill } from '@/types/planning'
import {
  allocationsToPercentMap,
  billToFormState,
  clampAllocations,
  mergePercentAllocations,
  normaliseBillForm,
} from '../planning'

describe('planning utils', () => {
  const sampleBill: Bill = {
    id: 'b1',
    name: 'Utilities',
    amountCents: 12345,
    dueDate: '2024-07-15',
    frequency: 'monthly',
    category: 'Home',
    origin: 'manual',
    accountId: 'acct-1',
    scenarioId: 's1',
  }

  it('converts a bill to a form state and back again', () => {
    const formState = billToFormState(sampleBill)
    expect(formState.amount).toBe('123.45')

    const normalised = normaliseBillForm({ ...formState, amount: '200.00' }, sampleBill)
    expect(normalised.amountCents).toBe(20000)
    expect(normalised.frequency).toBe('monthly')
  })

  it('clamps allocations to the overall cap', () => {
    const initial = { savings: 60, investing: 30 }
    const { next, total } = clampAllocations(initial, 'investing', 80)
    expect(next.investing).toBe(40)
    expect(total).toBe(100)
  })

  it('derives and merges percent allocations', () => {
    const allocations: Allocation[] = [
      { id: 'a1', target: 'savings:emergency', kind: 'percent', value: 25 },
      { id: 'a2', target: 'goal:vacation', kind: 'percent', value: 15 },
      { id: 'a3', target: 'bill:rent', kind: 'fixed', value: 50000 },
    ]

    const map = allocationsToPercentMap(allocations)
    expect(map).toEqual({ 'savings:emergency': 25, 'goal:vacation': 15 })

    const updatedPercentages = { ...map, 'goal:vacation': 20 }
    const merged = mergePercentAllocations(allocations, updatedPercentages, () => 'a4')
    const updatedGoal = merged.find((allocation) => allocation.target === 'goal:vacation')
    expect(updatedGoal?.value).toBe(20)
    expect(merged).toHaveLength(3)
  })

  it('throws when normalising invalid amounts', () => {
    expect(() => normaliseBillForm({ ...billToFormState(), amount: '-1', name: '', dueDate: '', frequency: '' })).toThrow()
  })
})
