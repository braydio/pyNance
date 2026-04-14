# Corner/Depth System Rollout Plan

## Purpose

This plan breaks the corner-radius and depth/border standardization work into three delivery phases and defines required artifacts for each phase.

## Global Requirements (apply to every phase)

Each phase is considered incomplete until all of the following are attached in the PR:

1. Before/after screen captures for the key routes listed in that phase.
2. A completed visual QA checklist that covers:
   - corner usage,
   - border contrast,
   - spacing rhythm,
   - focus visibility.
3. Documentation updates in both:
   - `docs/frontend/`
   - `docs/devnotes/`

## Phase 1 (Foundation)

### Scope

- Finalize design tokens for corner geometry and spacing rhythm.
- Finalize radius scale mapping to component tiers.
- Finalize depth and border-contrast token pairings.
- Update primitive components so they consume tokenized radius/depth values only.

### Key routes for required captures

- `/dashboard` (hero shell + at least one primitive-powered control)
- `/transactions` (primitive buttons/inputs/selects in active use)
- `/settings` (form controls + focus states)

### Exit criteria

- No new primitive ships with arbitrary `rounded-*` classes.
- Primitive components expose documented radius/depth variants backed by tokens.
- Token usage guidance is published and linked from docs index.

## Phase 2 (Core surfaces)

### Scope

- Migrate dashboard hero surfaces to approved radius/depth tiers.
- Migrate chart panels to approved surface tokens.
- Migrate table shells and sticky/table wrappers to approved radius/border rules.
- Migrate modal shells and modal action rows to approved radius/focus rules.

### Key routes for required captures

- `/dashboard` (hero + chart panels + summary cards)
- `/transactions` (table shells and modal open state)
- `/accounts` (table/list container surfaces)

### Exit criteria

- Hero, chart, table, and modal surfaces use only approved token combinations.
- Border contrast remains legible in light/dark contexts where supported.
- Focus rings remain visible against all migrated surfaces.

## Phase 3 (Secondary surfaces)

### Scope

- Migrate widgets and utility cards.
- Migrate forms not covered in phase 1 primitives or phase 2 core surfaces.
- Migrate utility screens and lower-traffic routes.

### Key routes for required captures

- `/investments` (secondary cards/widgets)
- `/planning` (form-heavy utilities)
- `/forecast` (supporting surfaces/widgets)

### Exit criteria

- Secondary routes match the same radius/depth hierarchy used on core routes.
- No regressions in focus visibility or spacing rhythm on utility screens.
- Any remaining exceptions are documented with rationale and follow-up owner.

## PR review gate (all phases)

PRs that touch frontend surfaces should be blocked from approval when any of these are missing:

- Missing before/after captures for impacted key routes.
- Missing visual QA checklist completion.
- Missing docs updates (`docs/frontend/` and `docs/devnotes/`).
- New arbitrary `rounded-*` usage without explicit justification and follow-up task.
