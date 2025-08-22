// frontend/src/services/planningService.ts

import { PlanningState, Scenario, Bill, Allocation } from "@/types/planning";
import { getBillsByAccount, getScenariosByAccount } from '@/composables/usePlanning'

const KEY = "pyNance:planning:v2";

export function loadPlanning(): PlanningState | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return migrate(JSON.parse(raw));
  } catch {
    return null;
  }
}

export function savePlanning(state: PlanningState) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // ignore quota issues
  }
}

function migrate(data: any): PlanningState | null {
  if (!data || typeof data !== "object") return null;
  // This is now handled in usePlanning.ts migrateState function
  // Keep minimal migration for compatibility
  if (!data.version) data.version = 1;
  return data as PlanningState;
}

/**
 * Return all stored planning scenarios.
 */
export async function listScenarios(): Promise<Scenario[]> {
  return loadPlanning()?.scenarios ?? [];
}

/**
 * Retrieve a single scenario by identifier.
 *
 * @param id - Scenario identifier.
 */
export async function getScenario(
  id: string
): Promise<Scenario | undefined> {
  const scenarios = await listScenarios();
  return scenarios.find((s) => s.id === id);
}

/**
 * Upsert a scenario and persist the planning state.
 *
 * @param scenario - Scenario data to store.
 */
export async function putScenario(scenario: Scenario): Promise<void> {
  const state =
    loadPlanning() ?? {
      version: 2,
      devMode: false,
      bills: [],
      scenarios: [],
      activeScenarioId: "",
      activeScenarioIdByAccount: {},
      lastSavedAt: "",
    };
  const idx = state.scenarios.findIndex((s) => s.id === scenario.id);
  if (idx >= 0) {
    state.scenarios[idx] = scenario;
  } else {
    state.scenarios.push(scenario);
  }
  state.lastSavedAt = new Date().toISOString();
  savePlanning(state);
}

// Account-scoped helpers

/**
 * Get bills for a specific account
 */
export function listBills(accountId: string): Bill[] {
  return getBillsByAccount(accountId)
}

/**
 * Upsert a bill and persist state
 */
export function upsertBill(bill: Bill): void {
  const state = loadPlanning() ?? {
    version: 2,
    devMode: false,
    bills: [],
    scenarios: [],
    activeScenarioId: "",
    activeScenarioIdByAccount: {},
    lastSavedAt: "",
  };
  
  const idx = state.bills.findIndex(b => b.id === bill.id)
  if (idx >= 0) {
    state.bills[idx] = bill
  } else {
    state.bills.push(bill)
  }
  
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}

/**
 * Delete a bill by ID
 */
export function deleteBill(id: string): void {
  const state = loadPlanning()
  if (!state) return
  
  state.bills = state.bills.filter(b => b.id !== id)
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}

/**
 * Get scenarios for a specific account
 */
export function listScenariosForAccount(accountId: string): Scenario[] {
  return getScenariosByAccount(accountId)
}

/**
 * Upsert a scenario and persist state
 */
export function upsertScenario(scenario: Scenario): void {
  const state = loadPlanning() ?? {
    version: 2,
    devMode: false,
    bills: [],
    scenarios: [],
    activeScenarioId: "",
    activeScenarioIdByAccount: {},
    lastSavedAt: "",
  };
  
  const idx = state.scenarios.findIndex(s => s.id === scenario.id)
  if (idx >= 0) {
    state.scenarios[idx] = scenario
  } else {
    state.scenarios.push(scenario)
  }
  
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}

/**
 * Delete a scenario by ID
 */
export function deleteScenario(id: string): void {
  const state = loadPlanning()
  if (!state) return
  
  state.scenarios = state.scenarios.filter(s => s.id !== id)
  // Clean up associated active scenario references
  Object.keys(state.activeScenarioIdByAccount).forEach(accountId => {
    if (state.activeScenarioIdByAccount[accountId] === id) {
      delete state.activeScenarioIdByAccount[accountId]
    }
  })
  
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}

/**
 * Get allocations for a specific scenario
 */
export function listAllocations(scenarioId: string): Allocation[] {
  const state = loadPlanning()
  if (!state) return []
  
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  return scenario?.allocations || []
}

/**
 * Upsert an allocation within a scenario
 */
export function upsertAllocation(scenarioId: string, allocation: Allocation): void {
  const state = loadPlanning()
  if (!state) return
  
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (!scenario) return
  
  const idx = scenario.allocations.findIndex(a => a.id === allocation.id)
  if (idx >= 0) {
    scenario.allocations[idx] = allocation
  } else {
    scenario.allocations.push(allocation)
  }
  
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}

/**
 * Delete an allocation by ID from a scenario
 */
export function deleteAllocation(scenarioId: string, allocationId: string): void {
  const state = loadPlanning()
  if (!state) return
  
  const scenario = state.scenarios.find(s => s.id === scenarioId)
  if (!scenario) return
  
  scenario.allocations = scenario.allocations.filter(a => a.id !== allocationId)
  
  state.lastSavedAt = new Date().toISOString()
  savePlanning(state)
}
