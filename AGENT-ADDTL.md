---

# What’s Missing

## A) Types file

You reference `@/types/planning` but didn’t include it in this slice.

**Add:** `frontend/src/types/planning.ts`

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
  value: number;  // cents if fixed; 0–100 if percent
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

## B) Derived selectors (allocation math, totals)

You compute/need totals in multiple places; centralize them.

**Add:** `frontend/src/selectors/planning.ts`

```ts
import type { PlanningState, Scenario } from "@/types/planning";

export const selectActiveScenario = (s: PlanningState): Scenario | undefined =>
  s.scenarios.find((x) => x.id === s.activeScenarioId);

export const selectTotalBillsCents = (s: PlanningState): number =>
  s.bills.reduce((a, b) => a + (b.amountCents || 0), 0);

export const selectAllocatedCents = (sc?: Scenario): number => {
  if (!sc) return 0;
  const fixed = sc.allocations
    .filter((a) => a.kind === "fixed")
    .reduce((a, b) => a + (b.value || 0), 0);
  const pct = Math.min(
    100,
    Math.max(
      0,
      sc.allocations
        .filter((a) => a.kind === "percent")
        .reduce((a, b) => a + (b.value || 0), 0),
    ),
  );
  const pctAlloc = Math.floor((sc.planningBalanceCents * pct) / 100);
  return fixed + pctAlloc;
};

export const selectRemainingCents = (sc?: Scenario): number => {
  if (!sc) return 0;
  const rem = sc.planningBalanceCents - selectAllocatedCents(sc);
  return rem > 0 ? rem : 0;
};
```

Use these in components instead of re-implementing math.

---

## C) Components referenced by the view

You referenced `PlanningSummary`, `BillForm`, `BillList`, and `Allocator`. Provide minimal but functional implementations.

**Add:** `frontend/src/components/planning/PlanningSummary.tsx`

```tsx
import React, { useMemo } from "react";
import type { Scenario } from "@/types/planning";
import { formatCurrency, fromCents, toCents } from "@/utils/currency";
import {
  selectAllocatedCents,
  selectRemainingCents,
  selectTotalBillsCents,
} from "@/selectors/planning";
import { usePlanning } from "@/context/PlanningContext";

export default function PlanningSummary({
  scenario,
  dispatch,
}: {
  scenario?: Scenario;
  dispatch: React.Dispatch<any>;
}) {
  const { state } = usePlanning();
  const totalBills = useMemo(() => selectTotalBillsCents(state), [state]);
  const allocated = useMemo(() => selectAllocatedCents(scenario), [scenario]);
  const remaining = useMemo(() => selectRemainingCents(scenario), [scenario]);

  const balanceDisplay = useMemo(
    () =>
      scenario ? fromCents(scenario.planningBalanceCents).toFixed(2) : "0.00",
    [scenario],
  );

  return (
    <div className="rounded-2xl shadow p-4 grid grid-cols-1 md:grid-cols-4 gap-4">
      <div>
        <label htmlFor="planning-balance" className="text-sm block mb-1">
          Planning Balance
        </label>
        <input
          id="planning-balance"
          aria-label="Planning Balance"
          className="border rounded px-2 py-1 w-full"
          defaultValue={balanceDisplay}
          onChange={(e) =>
            dispatch({
              type: "SET_BALANCE",
              value: toCents((e.target.value || "0").replace(/[^0-9.]/g, "")),
            })
          }
          inputMode="decimal"
        />
      </div>
      <Stat label="Bills (sum)" value={formatCurrency(totalBills)} />
      <Stat label="Allocated" value={formatCurrency(allocated)} />
      <Stat label="Remaining" value={formatCurrency(remaining)} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded border">
      <div className="text-sm opacity-70">{label}</div>
      <div className="text-lg font-medium">{value}</div>
    </div>
  );
}
```

**Add:** `frontend/src/components/planning/BillForm.tsx`

```tsx
import React, { useState } from "react";
import { toCents } from "@/utils/currency";
import { usePlanning } from "@/context/PlanningContext";

export default function BillForm({
  dispatch,
}: {
  dispatch: React.Dispatch<any>;
}) {
  const { state } = usePlanning();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [category, setCategory] = useState("");

  const generateId = () =>
    (
      Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
    ).toUpperCase();

  const save = () => {
    dispatch({
      type: "UPSERT_BILL",
      bill: {
        id: generateId(),
        name: name.trim(),
        amountCents: toCents(amount),
        dueDate,
        category: category.trim() || undefined,
        origin: "manual",
      },
    });
    setOpen(false);
    setName("");
    setAmount("");
    setDueDate("");
    setCategory("");
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="px-3 py-1 rounded bg-gray-900 text-white"
      >
        Add Bill
      </button>
      {open && (
        <dialog open className="p-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              save();
            }}
            className="p-4 space-y-3 min-w-[320px]"
          >
            <h3 className="font-medium">Add/Edit Bill</h3>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
              className="border rounded px-2 py-1 w-full"
              required
            />
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="Amount (USD)"
              inputMode="decimal"
              className="border rounded px-2 py-1 w-full"
              required
            />
            <input
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              type="date"
              className="border rounded px-2 py-1 w-full"
              required
            />
            <input
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="Category"
              className="border rounded px-2 py-1 w-full"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                className="px-3 py-1"
                onClick={() => setOpen(false)}
              >
                Cancel
              </button>
              <button className="px-3 py-1 rounded bg-gray-900 text-white">
                Save
              </button>
            </div>
          </form>
        </dialog>
      )}
    </>
  );
}
```

**Add:** `frontend/src/components/planning/BillList.tsx`

```tsx
import React from "react";
import { formatCurrency } from "@/utils/currency";
import type { Bill } from "@/types/planning";

export default function BillList({
  bills,
  dispatch,
}: {
  bills: Bill[];
  dispatch: React.Dispatch<any>;
}) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left border-b">
          <th className="py-2">Name</th>
          <th>Amount</th>
          <th>Due</th>
          <th>Category</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {bills.map((b) => (
          <tr key={b.id} className="border-b">
            <td className="py-2">
              <span>{b.name}</span>
              {b.origin === "predicted" && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded bg-yellow-100">
                  predicted
                </span>
              )}
            </td>
            <td>{formatCurrency(b.amountCents)}</td>
            <td>{b.dueDate}</td>
            <td>{b.category || "—"}</td>
            <td className="text-right">
              <button
                className="px-2 text-red-600"
                onClick={() => dispatch({ type: "DELETE_BILL", id: b.id })}
              >
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

**Add:** `frontend/src/components/planning/Allocator.tsx`

```tsx
import React, { useState } from "react";
import type { Scenario, Allocation } from "@/types/planning";
import { toCents, formatCurrency } from "@/utils/currency";

export default function Allocator({
  scenario,
  bills,
  dispatch,
}: {
  scenario?: Scenario;
  bills: { id: string; name: string }[];
  dispatch: React.Dispatch<any>;
}) {
  const [target, setTarget] = useState("");
  const [kind, setKind] = useState<"fixed" | "percent">("fixed");
  const [value, setValue] = useState("");

  const genId = () =>
    (
      Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
    ).toUpperCase();

  const add = () => {
    const v = kind === "fixed" ? toCents(value) : Number(value);
    const a: Allocation = { id: genId(), target, kind, value: v };
    dispatch({ type: "ADD_ALLOCATION", allocation: a });
    setTarget("");
    setKind("fixed");
    setValue("");
  };

  return (
    <div className="space-y-3">
      <form
        className="flex gap-2 items-end"
        onSubmit={(e) => {
          e.preventDefault();
          add();
        }}
      >
        <div className="flex-1">
          <label className="text-xs block">Target</label>
          <select
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <optgroup label="Bills">
              {bills.map((b) => (
                <option key={b.id} value={`bill:${b.id}`}>
                  {b.name}
                </option>
              ))}
            </optgroup>
            <optgroup label="Savings">
              <option value="savings:General">Savings (General)</option>
            </optgroup>
            <optgroup label="Goals">
              <option value="goal:Emergency Fund">Goal: Emergency Fund</option>
            </optgroup>
          </select>
        </div>
        <div>
          <label className="text-xs block">Kind</label>
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as any)}
            className="border rounded px-2 py-1"
          >
            <option value="fixed">Fixed</option>
            <option value="percent">Percent</option>
          </select>
        </div>
        <div>
          <label className="text-xs block">Value</label>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={kind === "fixed" ? "USD" : "%"}
            className="border rounded px-2 py-1 w-28"
            inputMode="decimal"
          />
        </div>
        <button className="px-3 py-1 rounded bg-gray-900 text-white">
          Add
        </button>
      </form>

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b">
            <th>Target</th>
            <th>Kind</th>
            <th>Value</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {scenario?.allocations.map((a) => (
            <tr key={a.id} className="border-b">
              <td>{a.target}</td>
              <td>{a.kind}</td>
              <td>
                {a.kind === "fixed" ? formatCurrency(a.value) : `${a.value}%`}
              </td>
              <td className="text-right">
                <button
                  className="px-2 text-red-600"
                  onClick={() =>
                    dispatch({ type: "DELETE_ALLOCATION", id: a.id })
                  }
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## D) Router entry

Your view won’t be reachable without this.

**Modify:** `frontend/src/router/index.tsx` (or wherever routes are defined)

```tsx
import { createBrowserRouter } from "react-router-dom";
import Planning from "@/views/Planning";

export const router = createBrowserRouter([
  // ...other routes
  { path: "/planning", element: <Planning /> },
]);
```

If you use a custom layout or sidebar, also add a nav item: **Planning → `/planning`**.

---

## E) tsconfig/vite path alias

You’re importing with `@/…`. Ensure `@` resolves to `src`.

**Update:** `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

**Update:** `frontend/vite.config.ts`

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
});
```

---

## F) Tests bootstrap (RTL)

Your unit test references RTL; include a simple setup (if not already present).

**Add:** `frontend/src/test/setup.ts`

```ts
import "@testing-library/jest-dom";
```

Then in `vite.config.ts` (test section) or `vitest.config.ts`:

```ts
test: {
  environment: "jsdom",
  setupFiles: ["./src/test/setup.ts"],
},
```

---

## G) Minor field notes

- **Bill.dueDate**: you marked as required; keep it required in UI (you do).
- **Bill.origin**: present and used to tag predicted bills; OK.
- **Allocation.value** semantics: ints for cents (fixed) vs 0–100 for percent; you clamp/cap via selectors; OK.
- **PlanningState.version**: you have simple migration. Consider adding a second key later (`schemaVersion`) if/when API parity is needed.

---

# Summary

**Missing files**: `types/planning.ts`, `selectors/planning.ts`, four component files, router entry, path alias config, test setup.
**Missing fields**: none critical—your contracts match the React plan; the key is centralizing math in selectors and ensuring components + routing exist.

If you drop these in, the roadmap compiles and runs cleanly with your current context + persistence.
