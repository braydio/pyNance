// frontend/src/composables/usePlanning.ts

import { reactive, readonly, watch } from 'vue'
import { loadPlanning, savePlanning } from '@/services/planningService'
import type { PlanningState } from '@/types/planning'

/**
 * Singleton planning state with automatic localStorage persistence.
 */
const defaultState: PlanningState = {
  version: 1,
  devMode: false,
  bills: [],
  scenarios: [],
  activeScenarioId: '',
  lastSavedAt: new Date().toISOString()
}

const state = reactive<PlanningState>(loadPlanning() ?? { ...defaultState })

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
