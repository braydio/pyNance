# TP-20261007-007: Planning Workflow Reauthor

**Packet ID:** TP-20261007-007  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-007-planning-workflow-reauthor.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-002  
**Priority:** High  
**Series:** UI/UX reauthor, packet 6 of 8  

## Objective

Turn Planning from an implementation/demo surface into a coherent planning workflow centered on upcoming obligations, available planning balance, allocations, and the next planning action.

## Confirmed current-state blocker

File: `frontend/src/views/Planning.vue`

The first main card currently renders internal notes directly to the user, including:

- "Here are a handful of notes and ideas I have for this page"
- speculative feature notes;
- "Gamefied somehow maybe?"
- "I will come back to this. I will not forget this for months."
- a placeholder bullet.

These are design/development notes, not product UI, and must be removed.

The view also places the BillList inside the same card as those notes while BillForm permanently occupies another large card even when there is no active create/edit task.

## Target hierarchy

1. planning status for the active scenario;
2. upcoming bills / obligations;
3. clear action to add or edit a bill;
4. allocation status;
5. form only when creating/editing;
6. secondary scenario/account context.

## Required changes

### 1. Remove all internal product notes from rendered UI

File:

- `frontend/src/views/Planning.vue`

Delete the visible notes/placeholder copy completely. If any idea remains valuable, move it to non-executable product documentation, not the rendered view.

Do not use invalid `<p1>` elements.

### 2. Make PlanningSummary the lead status surface

Files:

- `frontend/src/views/Planning.vue`
- `frontend/src/components/planning/PlanningSummary.vue`

Lead with the scenario's actionable state:

- planning balance;
- total upcoming bills;
- allocated amount/percent;
- remaining amount;
- any over-allocation or due-soon warning already derivable from current data.

Use one primary summary surface, not several equal cards.

### 3. Make upcoming bills the main work list

Files:

- `frontend/src/views/Planning.vue`
- `frontend/src/components/planning/BillList.vue`

BillList should be the main left-column content.

Improve scan order using current Bill fields:

- due date;
- bill name;
- amount;
- frequency;
- predicted/manual origin badge only when useful;
- edit/delete actions secondary to row content.

Sort/display should prioritize upcoming due date if the current component/state already supplies usable due dates. Do not silently change persistence ordering if it has behavioral meaning; sort a presentation copy when needed.

### 4. Show BillForm only during an explicit task

Files:

- `frontend/src/views/Planning.vue`
- `frontend/src/components/planning/BillForm.vue`

When `formVisible === false`, do not reserve a large empty form card. Create/Edit should open a focused inline panel, drawer-like region, or modal using existing primitives. Keep the current state/events/contracts.

Primary actions:

- Add bill
- Edit selected bill
- Cancel/Save

Remove duplicate "Create bill" / "Add bill" emphasis if both are visible simultaneously.

### 5. Clarify allocations as a second task

File:

- `frontend/src/components/planning/Allocator.vue`

Present allocations as "Where remaining money is assigned", with:

- total allocated;
- remaining percent/amount;
- clear invalid/over-100 state;
- sliders/inputs grouped under this explanation.

Do not make raw target identifiers such as `savings:emergency` feel like internal keys if display formatting can humanize them without changing stored values.

### 6. Scenario context

Keep account/scenario resolution behavior from `usePlanning`. Add a small context label when the page is scoped by `accountId`, but do not expose raw IDs as primary text.

## Tests

Update:

- `frontend/src/views/__tests__/Planning.spec.js`
- `frontend/src/views/__tests__/Planning.cy.js`
- `frontend/src/components/planning/__tests__/PlanningSummary.spec.ts`
- existing BillForm/Allocator tests if their presentation contracts change

Cover:

- internal notes no longer render;
- BillForm hidden until create/edit;
- one primary Add bill action;
- bill selection/edit still works;
- summary remains correct;
- allocation persistence unchanged.

## Non-goals

- Do not redesign planning backend persistence.
- Do not invent new scenario types.
- Do not implement gamification.
- Do not auto-create predicted bills in this packet.
- Do not change allocation math.

## Acceptance criteria

- [ ] No internal design/development notes are user-visible.
- [ ] PlanningSummary is the lead planning state.
- [ ] Upcoming bills are the primary work list.
- [ ] BillForm appears only during create/edit.
- [ ] Duplicate bill-creation CTAs are removed.
- [ ] Allocation labels and state are human-readable.
- [ ] Existing persistence/events remain intact.
- [ ] Focused Planning tests pass.

## Validation

```bash
cd frontend
npm run test -- --run src/views/__tests__/Planning.spec.js src/components/planning/__tests__/PlanningSummary.spec.ts
npm run lint
npm run build
```

## Completion report

Report removed placeholder UI, new information order, bill form behavior, allocation readability, preserved contracts, tests, and deviations.
