Here’s the **fully rewritten roadmap** with your required changes integrated (React + TypeScript + Vite + Tailwind + Vitest/RTL + Cypress).

---

# Planning Page — Implementation Plan (Repo-Accurate, React/TS)

## Conventions & Guardrails

- **Framework**: React + TypeScript + Vite + Tailwind.
- **State**: Global context with reducer (`PlanningProvider` + `usePlanning()` hook).
- **Typing**: TypeScript interfaces in `types/planning.ts`.
- **IDs**: `generateId()` helper (local random for prototype, UUID later for backend).
- **Currency**: store integer cents; format on render.
- **Dates**: ISO `YYYY-MM-DD` (local).
- **Persistence**: versioned `localStorage` via `frontend/src/services/planningService.ts` (migrate later to Flask backend).
- **Styling**: Tailwind.
- **Tests**: colocate unit tests under `frontend/src/views/__tests__/` using **Vitest + React Testing Library**.
- **E2E**: Cypress (already configured).

---

## Files to Add / Modify

```
frontend/src/views/Planning.tsx                        # NEW
frontend/src/router/index.tsx                          # MODIFY: add route
frontend/src/context/PlanningContext.tsx               # NEW (global state provider + hook)
frontend/src/services/planningService.ts               # NEW (versioned persistence)
frontend/src/utils/currency.ts                         # NEW (toCents/fromCents/formatCurrency)
frontend/src/components/planning/BillForm.tsx          # NEW
frontend/src/components/planning/BillList.tsx          # NEW
frontend/src/components/planning/Allocator.tsx         # NEW
frontend/src/components/planning/PlanningSummary.tsx   # NEW
frontend/src/views/__tests__/Planning.test.tsx         # NEW (Vitest + RTL)
frontend/cypress/e2e/planning.cy.ts                    # NEW (optional, end-to-end)
```

---

## Data Contracts

`frontend/src/types/planning.ts`

```ts
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
  value: number; // cents when fixed; 0–100 when percent
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
  lastSavedAt: string; // ISO
}
```

---

## Utilities

`frontend/src/utils/currency.ts`

```ts
export const toCents = (n: number | string): number =>
  Math.round(Number(n || 0) * 100);

export const fromCents = (c: number): number => Number(c || 0) / 100;

export const formatCurrency = (
  cents: number,
  locale = "en-US",
  currency = "USD",
): string =>
  new Intl.NumberFormat(locale, { style: "currency", currency }).format(
    fromCents(cents),
  );
```

---

## Persistence Service

`frontend/src/services/planningService.ts`

```ts
import { PlanningState } from "@/types/planning";

const KEY = "pyNance:planning:v1";

export function loadPlanning(): PlanningState | null {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    return migrate(data);
  } catch {
    return null;
  }
}

export function savePlanning(state: PlanningState) {
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    // ignore quota errors
  }
}

function migrate(data: any): PlanningState | null {
  if (!data || typeof data !== "object") return null;
  if (!data.version) data.version = 1;
  switch (data.version) {
    case 1:
      return data as PlanningState;
    default:
      return data as PlanningState;
  }
}
```

---

## Context (State + Reducer + Autosave)

`frontend/src/context/PlanningContext.tsx`

```tsx
import React, { createContext, useContext, useReducer, useEffect } from "react";
import { PlanningState, Bill, Allocation } from "@/types/planning";
import { loadPlanning, savePlanning } from "@/services/planningService";
import { toCents } from "@/utils/currency";

function generateId() {
  return (
    Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
  ).toUpperCase();
}

function defaultState(): PlanningState {
  const scenarioId = generateId();
  return {
    version: 1,
    devMode: false,
    bills: [],
    scenarios: [
      {
        id: scenarioId,
        name: "Default",
        planningBalanceCents: 0,
        allocations: [],
      },
    ],
    activeScenarioId: scenarioId,
    lastSavedAt: new Date().toISOString(),
  };
}

type Action =
  | { type: "SET_BALANCE"; value: number }
  | { type: "UPSERT_BILL"; bill: Bill }
  | { type: "DELETE_BILL"; id: string }
  | { type: "ADD_ALLOCATION"; allocation: Allocation }
  | { type: "UPDATE_ALLOCATION"; allocation: Allocation }
  | { type: "DELETE_ALLOCATION"; id: string }
  | { type: "SET_DEVMODE"; value: boolean }
  | { type: "SELECT_SCENARIO"; id: string }
  | { type: "ADD_SCENARIO"; name: string }
  | { type: "RENAME_SCENARIO"; id: string; name: string }
  | { type: "DELETE_SCENARIO"; id: string };

function reducer(state: PlanningState, action: Action): PlanningState {
  const clone = structuredClone(state) as PlanningState;
  const scenario = clone.scenarios.find((s) => s.id === clone.activeScenarioId);
  switch (action.type) {
    case "SET_BALANCE":
      if (scenario) scenario.planningBalanceCents = toCents(action.value);
      break;
    case "UPSERT_BILL":
      const idx = clone.bills.findIndex((b) => b.id === action.bill.id);
      if (idx >= 0) clone.bills[idx] = action.bill;
      else clone.bills.push(action.bill);
      break;
    case "DELETE_BILL":
      clone.bills = clone.bills.filter((b) => b.id !== action.id);
      break;
    case "ADD_ALLOCATION":
      scenario?.allocations.push(action.allocation);
      break;
    case "UPDATE_ALLOCATION":
      if (scenario) {
        const i = scenario.allocations.findIndex(
          (a) => a.id === action.allocation.id,
        );
        if (i >= 0) scenario.allocations[i] = action.allocation;
      }
      break;
    case "DELETE_ALLOCATION":
      if (scenario) {
        scenario.allocations = scenario.allocations.filter(
          (a) => a.id !== action.id,
        );
      }
      break;
    case "SET_DEVMODE":
      clone.devMode = action.value;
      break;
    case "SELECT_SCENARIO":
      clone.activeScenarioId = action.id;
      break;
    case "ADD_SCENARIO":
      const sc = {
        id: generateId(),
        name: action.name,
        planningBalanceCents: 0,
        allocations: [],
      };
      clone.scenarios.push(sc);
      clone.activeScenarioId = sc.id;
      break;
    case "RENAME_SCENARIO":
      clone.scenarios.find((s) => s.id === action.id)!.name = action.name;
      break;
    case "DELETE_SCENARIO":
      clone.scenarios = clone.scenarios.filter((s) => s.id !== action.id);
      if (clone.activeScenarioId === action.id) {
        clone.activeScenarioId = clone.scenarios[0]?.id || "";
      }
      break;
  }
  clone.lastSavedAt = new Date().toISOString();
  return clone;
}

const PlanningContext = createContext<{
  state: PlanningState;
  dispatch: React.Dispatch<Action>;
}>({ state: defaultState(), dispatch: () => {} });

export function PlanningProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(
    reducer,
    loadPlanning() || defaultState(),
  );

  useEffect(() => {
    savePlanning(state);
  }, [state]);

  return (
    <PlanningContext.Provider value={{ state, dispatch }}>
      {children}
    </PlanningContext.Provider>
  );
}

export function usePlanning() {
  return useContext(PlanningContext);
}
```

---

## View

`frontend/src/views/Planning.tsx`

```tsx
import React from "react";
import { usePlanning } from "@/context/PlanningContext";
import PlanningSummary from "@/components/planning/PlanningSummary";
import BillForm from "@/components/planning/BillForm";
import BillList from "@/components/planning/BillList";
import Allocator from "@/components/planning/Allocator";

export default function Planning() {
  const { state, dispatch } = usePlanning();
  const scenario = state.scenarios.find((s) => s.id === state.activeScenarioId);

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Planning</h1>
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={state.devMode}
              onChange={(e) =>
                dispatch({ type: "SET_DEVMODE", value: e.target.checked })
              }
            />
            <span>Dev/Forecast Mode</span>
          </label>
          <span className="text-sm opacity-70">
            Saved: {new Date(state.lastSavedAt).toLocaleString()}
          </span>
        </div>
      </header>

      <PlanningSummary scenario={scenario} dispatch={dispatch} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="rounded-2xl shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-medium">Bills & Obligations</h2>
            <BillForm dispatch={dispatch} />
          </div>
          <BillList bills={state.bills} dispatch={dispatch} />
        </section>

        <section className="rounded-2xl shadow p-4">
          <h2 className="text-lg font-medium mb-3">Allocator</h2>
          <Allocator
            scenario={scenario}
            dispatch={dispatch}
            bills={state.bills}
          />
        </section>
      </div>
    </div>
  );
}
```

---

## Allocation Rules

- Apply **fixed allocations first** (sum of fixed cents).
- Apply **percent allocations** on planning balance, capped at 100%.
- Remaining is clamped to ≥0.
- Predicted bills replace previous on each dev-mode run and are visually tagged.

---

## Testing (Vitest + React Testing Library)

`frontend/src/views/__tests__/Planning.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { PlanningProvider } from "@/context/PlanningContext";
import Planning from "@/views/Planning";
import userEvent from "@testing-library/user-event";

test("renders planning page and updates balance", async () => {
  render(
    <PlanningProvider>
      <Planning />
    </PlanningProvider>,
  );

  expect(screen.getByText(/Planning/)).toBeInTheDocument();

  const input = screen.getByLabelText(/Planning Balance/i) as HTMLInputElement;
  await userEvent.clear(input);
  await userEvent.type(input, "500");

  expect(input.value).toBe("500");
});
```

---

## Milestones & Done Criteria

- **M1 – Scaffolding**: Route + `Planning.tsx` renders; context + persistence wired; summary shows zeros; autosave timestamp visible.
- **M2 – Bills**: Add/Edit/Delete via `BillForm`/`BillList`; totals correct; predicted tag renders.
- **M3 – Allocator**: Add/edit/delete allocations; remaining updates per rules.
- **M4 – Dev Mode**: Toggle persists; predicted bills injected/replaced.
- **M5 – Tests**: Vitest unit tests passing; Cypress optional E2E.

---

This roadmap is now **repo-aligned**: React + TS + Tailwind, with state in Context, persistence in localStorage, Vitest/RTL tests, and a backend path defined.
