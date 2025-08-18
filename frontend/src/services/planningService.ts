// frontend/src/services/planningService.ts

import { PlanningState } from "@/types/planning";

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
