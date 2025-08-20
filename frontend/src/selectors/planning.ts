// frontend/src/selectors/planning.ts

import type { PlanningState, Scenario } from "@/types/planning";

export const selectActiveScenario = (s: PlanningState): Scenario | undefined =>
  s.scenarios.find(x => x.id === s.activeScenarioId);

export const selectTotalBillsCents = (s: PlanningState): number =>
  s.bills.reduce((a, b) => a + (b.amountCents || 0), 0);

export const selectAllocatedCents = (sc?: Scenario): number => {
  if (!sc) return 0;
  const fixed = sc.allocations.filter(a => a.kind === "fixed")
    .reduce((a, b) => a + (b.value || 0), 0);
  const pct = Math.min(
    100,
    Math.max(0, sc.allocations.filter(a => a.kind === "percent")
      .reduce((a, b) => a + (b.value || 0), 0))
  );
  const pctAlloc = Math.floor((sc.planningBalanceCents * pct) / 100);
  return fixed + pctAlloc;
};

export const selectRemainingCents = (sc?: Scenario): number => {
  if (!sc) return 0;
  const rem = sc.planningBalanceCents - selectAllocatedCents(sc);
  return rem > 0 ? rem : 0;
};
