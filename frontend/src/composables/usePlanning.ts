// frontend/src/composables/usePlanning.ts

import { reactive, readonly, watch } from 'vue'
import {
  loadPlanning,
  savePlanning,
  createBill as apiCreateBill,
  updateBill as apiUpdateBill,
  deleteBill as apiDeleteBill,
  replaceScenarioAllocations as apiReplaceScenarioAllocations,
} from '@/services/planningService'
import type { Allocation, Bill, PlanningMode, PlanningState, Scenario } from '@/types/planning'
import type { BillFormSubmitPayload } from '@/utils/planning'

const configuredMode = (import.meta.env.VITE_PLANNING_MODE ?? '').toLowerCase()
const envMode: PlanningMode = configuredMode === 'api' ? 'api' : 'local'

/**
 * Singleton planning state with automatic localStorage persistence.
 */
const defaultState: PlanningState = {
  version: 4,
  devMode: false,
  mode: envMode,
  bills: [],
  scenarios: [],
  activeScenarioId: '',
  activeScenarioIdByAccount: {},
  lastSavedAt: new Date().toISOString()
}

/**
 * Migrate planning state from older versions
 */
function migrateState(loadedState: any): PlanningState {
  let working = loadedState
  if (!working || typeof working !== 'object') {
    working = {}
  }

  if ((working.version ?? 1) < 2) {
    const migratedState = { ...working }

    migratedState.bills = (migratedState.bills || []).map((bill: any) => ({
      ...bill,
      accountId: bill.accountId || '',
      scenarioId: bill.scenarioId || undefined,
    }))

    migratedState.scenarios = (migratedState.scenarios || []).map((scenario: any) => ({
      ...scenario,
      accountId: scenario.accountId || '',
    }))

    migratedState.activeScenarioIdByAccount = {}
    if (migratedState.activeScenarioId) {
      migratedState.activeScenarioIdByAccount[''] = migratedState.activeScenarioId
    }

    migratedState.version = 2
    working = migratedState
  }

  if ((working.version ?? 1) < 3) {
    const migratedState = { ...working }

    migratedState.bills = (migratedState.bills || []).map((bill: any) => ({
      ...bill,
      frequency: bill.frequency || 'monthly',
    }))

    migratedState.scenarios = (migratedState.scenarios || []).map((scenario: any) => ({
      ...scenario,
      currencyCode: scenario.currencyCode || 'USD',
    }))

    migratedState.version = 3
    working = migratedState
  }

  if ((working.version ?? 1) < 4) {
    const migratedState = { ...working }
    migratedState.mode = migratedState.mode ?? envMode
    migratedState.version = 4
    working = migratedState
  }

  const accountMap =
    working.activeScenarioIdByAccount && typeof working.activeScenarioIdByAccount === 'object'
      ? working.activeScenarioIdByAccount
      : {}

  return {
    ...defaultState,
    ...working,
    version: 4,
    mode: (working.mode as PlanningMode) ?? envMode,
    bills: Array.isArray(working.bills) ? working.bills : [],
    scenarios: Array.isArray(working.scenarios) ? working.scenarios : [],
    activeScenarioIdByAccount: { ...defaultState.activeScenarioIdByAccount, ...accountMap },
    lastSavedAt:
      typeof working.lastSavedAt === 'string' ? working.lastSavedAt : new Date().toISOString(),
  }
}

const state = reactive<PlanningState>(migrateState(loadPlanning()))

// Persist changes whenever state mutates.
watch(
  state,
  () => {
    state.version = defaultState.version
    state.mode = state.mode ?? envMode
    state.lastSavedAt = new Date().toISOString()
    savePlanning(state)
  },
  { deep: true }
)

/**
 * Access the reactive planning state.
 * Consumers receive a read-only snapshot to discourage direct mutation.
 */
export function usePlanning() {
  return { state: readonly(state) }
}

/**
 * Merge partial updates into the planning state.
 */
export function updatePlanning(patch: Partial<PlanningState>) {
  Object.assign(state, patch)
}

/**
 * Override the planning mode at runtime.
 */
export function setPlanningMode(mode: PlanningMode) {
  if (mode !== 'local' && mode !== 'api') {
    return
  }
  updatePlanning({ mode })
}

function cloneState(): PlanningState {
  return JSON.parse(JSON.stringify(state)) as PlanningState
}

function restoreState(snapshot: PlanningState) {
  updatePlanning({
    bills: snapshot.bills,
    scenarios: snapshot.scenarios,
    activeScenarioId: snapshot.activeScenarioId,
    activeScenarioIdByAccount: { ...snapshot.activeScenarioIdByAccount },
  })
}

function commitBill(persisted: Bill, matchId: string) {
  const hasMatch = state.bills.some((bill) => bill.id === matchId)
  const nextBills = hasMatch
    ? state.bills.map((bill) => (bill.id === matchId ? persisted : bill))
    : [...state.bills, persisted]
  updatePlanning({ bills: nextBills })
}

function generateId(prefix: string): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `${prefix}-${Date.now()}`
}

/**
 * Ensure an account-scoped scenario exists and becomes active.
 */
export function ensureScenarioForAccount(
  accountId = '',
  options: { currencyCode?: string; name?: string } = {},
): Scenario {
  const mappedId = accountId
    ? state.activeScenarioIdByAccount[accountId]
    : state.activeScenarioId
  let scenario = mappedId
    ? state.scenarios.find((candidate) => candidate.id === mappedId)
    : undefined

  if (!scenario && accountId) {
    scenario = state.scenarios.find((candidate) => candidate.accountId === accountId)
  }

  if (!scenario) {
    scenario = {
      id: generateId('scenario'),
      name: options.name ?? (accountId ? `Plan for ${accountId}` : 'Baseline plan'),
      planningBalanceCents: 0,
      allocations: [],
      accountId,
      currencyCode: options.currencyCode ?? 'USD',
    }
    updatePlanning({ scenarios: [...state.scenarios, scenario] })
  }

  setActiveScenarioId(accountId, scenario.id)
  return scenario
}

/**
 * Persist a bill using the configured planning mode.
 */
export async function persistBill(payload: BillFormSubmitPayload): Promise<Bill> {
  const scenarioId = payload.scenarioId ?? state.activeScenarioId
  if (!scenarioId) {
    throw new Error('Cannot persist bill without an active scenario')
  }

  const scenario =
    state.scenarios.find((candidate) => candidate.id === scenarioId) ??
    ensureScenarioForAccount(payload.accountId ?? '', { currencyCode: 'USD' })

  const accountId = payload.accountId ?? scenario.accountId
  const baseBill: Bill = {
    id: payload.id ?? generateId('bill'),
    name: payload.name,
    amountCents: payload.amountCents,
    dueDate: payload.dueDate,
    frequency: payload.frequency,
    category: payload.category,
    origin: payload.origin ?? 'manual',
    accountId,
    scenarioId,
  }

  const isUpdate = Boolean(payload.id)
  const snapshot = cloneState()
  const nextBills = isUpdate
    ? state.bills.map((bill) => (bill.id === baseBill.id ? baseBill : bill))
    : [...state.bills, baseBill]

  updatePlanning({ bills: nextBills })

  if (state.mode === 'local') {
    return baseBill
  }

  try {
    if (isUpdate) {
      const response = await apiUpdateBill(baseBill.id, {
        name: baseBill.name,
        amountCents: baseBill.amountCents,
        dueDate: baseBill.dueDate,
        frequency: baseBill.frequency,
        category: baseBill.category,
        origin: baseBill.origin,
        accountId: baseBill.accountId,
        scenarioId: baseBill.scenarioId,
      })
      commitBill(response, baseBill.id)
      return response
    }

    const { id: _omitId, ...createPayload } = baseBill
    const response = await apiCreateBill(createPayload)
    commitBill(response, baseBill.id)
    return response
  } catch (error) {
    restoreState(snapshot)
    throw error
  }
}

/**
 * Remove a bill while respecting optimistic updates in API mode.
 */
export async function removeBill(billId: string): Promise<void> {
  const snapshot = cloneState()
  updatePlanning({ bills: state.bills.filter((bill) => bill.id !== billId) })

  if (state.mode === 'local') {
    return
  }

  try {
    await apiDeleteBill(billId)
  } catch (error) {
    restoreState(snapshot)
    throw error
  }
}

/**
 * Persist scenario allocations using the active persistence mode.
 */
export async function persistScenarioAllocations(
  scenarioId: string,
  allocations: Allocation[],
): Promise<Allocation[]> {
  const snapshot = cloneState()
  updatePlanning({
    scenarios: state.scenarios.map((scenario) =>
      scenario.id === scenarioId ? { ...scenario, allocations } : scenario,
    ),
  })

  if (state.mode === 'local') {
    return allocations
  }

  try {
    const response = await apiReplaceScenarioAllocations(scenarioId, allocations)
    updatePlanning({
      scenarios: state.scenarios.map((scenario) =>
        scenario.id === scenarioId ? { ...scenario, allocations: response } : scenario,
      ),
    })
    return response
  } catch (error) {
    restoreState(snapshot)
    throw error
  }
}

/**
 * Reset the planning singleton. Primarily used by tests to ensure isolation.
 */
export function resetPlanningState(nextState?: Partial<PlanningState>) {
  const merged = {
    ...defaultState,
    ...nextState,
    bills: nextState?.bills ?? defaultState.bills,
    scenarios: nextState?.scenarios ?? defaultState.scenarios,
    activeScenarioIdByAccount:
      nextState?.activeScenarioIdByAccount ?? defaultState.activeScenarioIdByAccount,
  }

  state.version = merged.version
  state.devMode = merged.devMode
  state.mode = merged.mode
  state.bills = [...merged.bills]
  state.scenarios = [...merged.scenarios]
  state.activeScenarioId = merged.activeScenarioId
  state.activeScenarioIdByAccount = { ...merged.activeScenarioIdByAccount }
  state.lastSavedAt = merged.lastSavedAt ?? new Date().toISOString()
}

// Account-aware selectors and helpers

/**
 * Get bills for a specific account
 */
export function getBillsByAccount(accountId: string) {
  return state.bills.filter(bill => bill.accountId === accountId)
}

/**
 * Get scenarios for a specific account
 */
export function getScenariosByAccount(accountId: string) {
  return state.scenarios.filter(scenario => scenario.accountId === accountId)
}

/**
 * Get the active scenario ID for a specific account
 */
export function getActiveScenarioId(accountId: string): string {
  return state.activeScenarioIdByAccount[accountId] || ''
}

/**
 * Set the active scenario ID for a specific account
 */
export function setActiveScenarioId(accountId: string, scenarioId: string) {
  updatePlanning({
    activeScenarioId: scenarioId,
    activeScenarioIdByAccount: {
      ...state.activeScenarioIdByAccount,
      [accountId]: scenarioId,
    },
  })
}

/**
 * Get the active scenario for a specific account
 */
export function getActiveScenario(accountId: string) {
  const activeScenarioId = getActiveScenarioId(accountId)
  return state.scenarios.find(scenario => 
    scenario.id === activeScenarioId && scenario.accountId === accountId
  )
}

/**
 * Get allocations for a specific scenario
 */
export function getAllocationsByScenario(scenarioId: string) {
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  return scenario?.allocations || []
}
