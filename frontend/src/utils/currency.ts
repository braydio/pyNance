// frontend/src/utils/currency.ts

export type BillOrigin = "manual" | "predicted";
export type AllocationType = "fixed" | "percent";

export interface Bill {
  id: string;
  name: string;
  amountCents: number;
  dueDate: string; // YYYY-MM-DD
  category?: string;
  origin: BillOrigin;
}

export interface Allocation {
  id: string;
  target: string; // "bill:<billId>" | "savings:<name>" | "goal:<name>"
  kind: AllocationType;
  value: number; // cents if fixed, 0–100 if percent
}

export interface Scenario {
  id: string;
  name: string;
  planningBalanceCents: number;
  allocations: Allocation[];
}

export interface PlanningState {
  version: number;
  devMode: boolean;
  bills: Bill[];
  scenarios: Scenario[];
  activeScenarioId: string;
  lastSavedAt: string;
}
