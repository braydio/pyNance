// frontend/src/types/planning.ts

export type BillOrigin = "manual" | "predicted";
export type BillFrequency = "once" | "weekly" | "monthly" | "yearly";
export type AllocationType = "fixed" | "percent";
export type PlanningMode = "local" | "api";

export interface Bill {
  id: string;
  name: string;
  amountCents: number;
  dueDate: string; // YYYY-MM-DD
  frequency: BillFrequency;
  category?: string;
  origin: BillOrigin;
  accountId: string;
  scenarioId?: string;
}

export interface Allocation {
  id: string;
  target: string; // "bill:<billId>" | "savings:<name>" | "goal:<name>"
  kind: AllocationType;
  value: number;  // cents if fixed; 0–100 if percent
}

export interface Scenario {
  id: string;
  name: string;
  planningBalanceCents: number;
  allocations: Allocation[];
  accountId: string;
  currencyCode: string;
}

export interface PlanningState {
  version: number;
  devMode: boolean;
  mode: PlanningMode;
  bills: Bill[];
  scenarios: Scenario[];
  activeScenarioId: string;
  activeScenarioIdByAccount: Record<string, string>;
  lastSavedAt: string; // ISO
}

