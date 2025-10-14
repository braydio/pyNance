import { beforeEach, describe, expect, it, vi } from 'vitest'

const serviceMocks = vi.hoisted(() => ({
  loadPlanning: vi.fn(() => null),
  savePlanning: vi.fn(),
  createBill: vi.fn(async (payload) => ({ id: payload.id ?? 'server-generated', ...payload })),
  updateBill: vi.fn(async (id, payload) => ({ id, ...payload })),
  deleteBill: vi.fn(async () => {}),
  replaceScenarioAllocations: vi.fn(async (_scenarioId, allocations) => allocations),
}))

vi.mock('@/services/planningService', () => serviceMocks)

import {
  ensureScenarioForAccount,
  persistBill,
  persistScenarioAllocations,
  removeBill,
  resetPlanningState,
  setPlanningMode,
  usePlanning,
} from '../usePlanning'
import type { Allocation } from '@/types/planning'

describe('usePlanning composable', () => {
  const { state } = usePlanning()

  beforeEach(() => {
    resetPlanningState({
      version: 4,
      devMode: false,
      mode: 'local',
      bills: [],
      scenarios: [],
      activeScenarioId: '',
      activeScenarioIdByAccount: {},
      lastSavedAt: new Date('2024-01-01').toISOString(),
    })
    serviceMocks.savePlanning.mockClear()
    serviceMocks.createBill.mockClear()
    serviceMocks.updateBill.mockClear()
    serviceMocks.deleteBill.mockClear()
    serviceMocks.replaceScenarioAllocations.mockClear()
  })

  it('persists bills locally when in local mode', async () => {
    const scenario = ensureScenarioForAccount('acct-local')

    await persistBill({
      name: 'Internet',
      amountCents: 6500,
      dueDate: '2024-08-01',
      frequency: 'monthly',
      category: 'Utilities',
      accountId: scenario.accountId,
      scenarioId: scenario.id,
    })

    expect(state.bills).toHaveLength(1)
    expect(state.bills[0].name).toBe('Internet')
    expect(serviceMocks.createBill).not.toHaveBeenCalled()
  })

  it('removes bills and propagates to the service in api mode', async () => {
    setPlanningMode('api')
    const scenario = ensureScenarioForAccount('acct-api')
    const bill = await persistBill({
      name: 'Gym',
      amountCents: 4500,
      dueDate: '2024-08-15',
      frequency: 'monthly',
      category: 'Health',
      accountId: scenario.accountId,
      scenarioId: scenario.id,
    })

    await removeBill(bill.id)

    expect(serviceMocks.deleteBill).toHaveBeenCalledWith(bill.id)
    expect(state.bills).toHaveLength(0)
  })

  it('rolls back bill updates when the api rejects the change', async () => {
    setPlanningMode('api')
    const scenario = ensureScenarioForAccount('acct-rollback')
    const bill = await persistBill({
      name: 'Phone',
      amountCents: 8000,
      dueDate: '2024-08-20',
      frequency: 'monthly',
      category: 'Utilities',
      accountId: scenario.accountId,
      scenarioId: scenario.id,
    })

    serviceMocks.updateBill.mockRejectedValueOnce(new Error('api failure'))

    await expect(
      persistBill({
        id: bill.id,
        name: 'Phone Unlimited',
        amountCents: 8200,
        dueDate: '2024-08-20',
        frequency: 'monthly',
        category: 'Utilities',
        accountId: scenario.accountId,
        scenarioId: scenario.id,
      }),
    ).rejects.toThrow('api failure')

    expect(state.bills[0].name).toBe('Phone')
  })

  it('persists scenario allocations and rolls back on failure', async () => {
    setPlanningMode('api')
    const scenario = ensureScenarioForAccount('acct-alloc')
    const initial: Allocation[] = [
      { id: 'alloc-1', target: 'savings:emergency', kind: 'percent', value: 25 },
    ]
    await persistScenarioAllocations(scenario.id, initial)

    serviceMocks.replaceScenarioAllocations.mockRejectedValueOnce(new Error('alloc failure'))
    const next: Allocation[] = [
      { id: 'alloc-1', target: 'savings:emergency', kind: 'percent', value: 30 },
    ]

    await expect(persistScenarioAllocations(scenario.id, next)).rejects.toThrow('alloc failure')
    expect(state.scenarios[0].allocations).toEqual(initial)
  })
})
