// frontend/src/composables/usePlanning.ts

import { reactive, readonly, watch } from 'vue'
import { loadPlanning, savePlanning } from '@/services/planningService'
import type { PlanningState } from '@/types/planning'

/**
 * Singleton planning state with automatic localStorage persistence.
 */
const defaultState: PlanningState = {
  version: 2,
  devMode: false,
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
  if (!loadedState || typeof loadedState !== 'object') {
    return { ...defaultState }
  }

  // Migration from version 1 to 2
  if (loadedState.version < 2) {
    const migratedState = { ...loadedState }
    
    // Add accountId to existing bills
    migratedState.bills = (migratedState.bills || []).map((bill: any) => ({
      ...bill,
      accountId: bill.accountId || '',
      scenarioId: bill.scenarioId || undefined
    }))
    
    // Add accountId to existing scenarios
    migratedState.scenarios = (migratedState.scenarios || []).map((scenario: any) => ({
      ...scenario,
      accountId: scenario.accountId || ''
    }))
    
    // Migrate activeScenarioId to activeScenarioIdByAccount
    migratedState.activeScenarioIdByAccount = {}
    if (migratedState.activeScenarioId) {
      migratedState.activeScenarioIdByAccount[''] = migratedState.activeScenarioId
    }
    
    migratedState.version = 2
    return migratedState
  }
  
  return loadedState
}

const state = reactive<PlanningState>(migrateState(loadPlanning()))

// Persist changes whenever state mutates.
watch(
  state,
  () => {
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
  state.activeScenarioIdByAccount[accountId] = scenarioId
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
