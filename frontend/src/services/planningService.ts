// frontend/src/services/planningService.ts

import { PlanningState, Scenario } from "@/types/planning";

const KEY = "pyNance:planning:v1";

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
      version: 1,
      devMode: false,
      bills: [],
      scenarios: [],
      activeScenarioId: "",
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
