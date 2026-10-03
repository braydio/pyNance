# Task Packet System

This directory is the canonical home for executable implementation task packets in pyNance.

Agents must not create new task packets under `docs/devnotes/`, issue comments, scratch files, or arbitrary feature folders. Those locations may link here, but the packet itself lives here.

## Canonical layout

```text
docs/task-packets/
├── README.md
├── INDEX.md
├── TRACKER.md
├── active/
│   └── TP-YYYYMMDD-NNN-kebab-case-slug.md
├── completed/
│   └── TP-YYYYMMDD-NNN-kebab-case-slug.md
└── archived/
    └── TP-YYYYMMDD-NNN-kebab-case-slug.md
```

Lifecycle folders:

- `active/`: Draft, Ready, In Progress, or Blocked.
- `completed/`: implemented and validated.
- `archived/`: Superseded, Cancelled, or intentionally abandoned.

Create `completed/` or `archived/` when the first packet enters that state. Do not duplicate a packet across lifecycle folders.

## Packet naming

Every packet gets one immutable ID:

```text
TP-YYYYMMDD-NNN
```

Filename:

```text
TP-YYYYMMDD-NNN-kebab-case-slug.md
```

Rules:

- `YYYYMMDD` is the packet creation date.
- `NNN` starts at `001` and increments only when multiple packets are created on the same date.
- The ID never changes when the packet moves between lifecycle folders.
- The slug may be shortened only during an explicit rename, and all index/tracker links must be updated in the same change.
- Never reuse an old packet ID.

## Controlled statuses

Use exactly one of:

- `Draft`
- `Ready`
- `In Progress`
- `Blocked`
- `Complete`
- `Superseded`
- `Cancelled`

Folder and status must agree:

| Status | Folder |
| --- | --- |
| Draft | active |
| Ready | active |
| In Progress | active |
| Blocked | active |
| Complete | completed |
| Superseded | archived |
| Cancelled | archived |

## Required packet header

Every packet begins with:

```markdown
# TP-YYYYMMDD-NNN: Human-readable title

**Packet ID:** TP-YYYYMMDD-NNN
**Status:** Ready
**Created:** YYYY-MM-DD
**Last updated:** YYYY-MM-DD
**Repository:** braydio/pyNance
**Target branch:** main
**Canonical path:** `docs/task-packets/active/TP-...`
**Workstream size:** One implementation packet
**Depends on:** None
```

Add Priority only when it materially affects ordering.

## Execution flow for agents

1. Read root `AGENTS.md`.
2. Read this file.
3. Read `TRACKER.md` and locate the assigned Packet ID.
4. Open the packet only from its canonical path in `INDEX.md`.
5. Confirm its status is executable: `Ready`, `In Progress`, or explicitly assigned `Blocked` recovery work.
6. Before coding, validate only the packet's named files/functions against current `main`. Do not perform a repo-wide rediscovery pass unless the packet is demonstrably stale.
7. Change the packet status and `TRACKER.md` to `In Progress` when implementation starts.
8. Implement in the packet's stated order. Stay inside its non-goals unless a concrete blocker requires a documented deviation.
9. Run focused validation first, then the packet's completion/full validation.
10. Record exact blockers or deviations rather than silently weakening requirements.
11. On completion:
    - set packet Status to `Complete`;
    - update Last updated;
    - move it to `docs/task-packets/completed/`;
    - update `INDEX.md` and `TRACKER.md` in the same change;
    - include test results in the implementation report.
12. If superseded/cancelled, move it to `archived/` and identify the replacement packet if one exists.

Do not implement from legacy pointer files in `docs/devnotes/`.

## TRACKER vs INDEX

`INDEX.md` is the canonical discovery catalog. It answers: **what packets exist and where are they?**

`TRACKER.md` is the live execution ledger. It answers: **what is active, what state is it in, what blocks it, and what should run next?**

Both must be updated when a packet is created, moved, completed, blocked, superseded, or cancelled.

## Authoring standard

Task packets are executable interfaces, not brainstorming notes.

Before writing a packet:

1. Inspect the current implementation on `main`.
2. Identify the exact files, functions, routes, components, models, migrations, and tests involved.
3. Separate confirmed facts from recommended changes.
4. Resolve obvious architecture questions before handing the packet to another agent.

A good packet should contain, when applicable:

- exact repository-relative file paths;
- exact function/class/route/component names;
- current code excerpts for the seam being changed;
- recommended replacement code or pseudocode when practical;
- explicit data/API contracts;
- implementation order;
- migration strategy and compatibility behavior;
- focused tests and exact validation commands;
- acceptance criteria;
- non-goals;
- dependencies/locks;
- expected completion report;
- an explicit packet count and dependency order when the work is intentionally split across multiple packets.

### Minimize token burn and drift

Prefer:

```text
File: backend/app/services/foo.py
Function: build_foo()

Current:
    ...

Target:
    ...
```

over:

```text
Find the relevant backend service and improve the behavior.
```

Additional rules:

- Give exact paths before prose descriptions.
- Use function/symbol names as primary anchors. Line numbers are optional hints because they drift.
- Include real code recommendations when the correct shape is known.
- Reuse existing helpers and contracts instead of instructing the implementer to invent parallel systems.
- State `Do not rediscover` boundaries when the relevant surface has already been traced.
- Do not ask the implementation agent to make product/architecture decisions the packet author can settle first.
- Do not inflate a packet with unrelated cleanup.
- One packet should represent one coherent, independently testable workstream. Split work when separate locks, deploy boundaries, or independently shippable contracts make that safer.
- When new runtime evidence changes the diagnosis, update the canonical packet directly and bump `Last updated`. Do not leave the real correction only in chat or a side note.
- If a recommendation is uncertain, say exactly what must be verified and where. Do not present guesses as repository facts.

## Lightweight packet template

```markdown
# TP-YYYYMMDD-NNN: Title

<header>

## Objective
One concrete outcome.

## Confirmed current state
Exact files/symbols and relevant current behavior.

## Required changes
### 1. path/to/file
Current seam, target behavior, recommended code.

## Tests
Exact files/cases/commands.

## Non-goals
Explicit boundaries.

## Implementation order
1. ...
2. ...

## Acceptance criteria
- [ ] ...

## Completion report
Files changed, contracts implemented, tests, deviations.
```

Keep this system boring, deterministic, and easy for the next agent to enter without archaeology.
