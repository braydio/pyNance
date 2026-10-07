# TP-20261007-002: UI Hierarchy Foundation + App Shell

**Packet ID:** TP-20261007-002  
**Status:** Ready  
**Created:** 2026-10-07  
**Last updated:** 2026-10-07  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** `docs/task-packets/active/TP-20261007-002-ui-hierarchy-foundation-app-shell.md`  
**Workstream size:** One implementation packet  
**Depends on:** TP-20261007-001  
**Priority:** High  
**Series:** UI/UX reauthor, packet 1 of 8  

## Objective

Establish a calmer, decision-oriented visual system and app shell before reauthoring individual views. The goal is lower reading effort, clearer information priority, fewer nested cards, and a consistent visual grammar that later packets can reuse instead of inventing page-local styling.

## Product hierarchy rules to lock

Implement and document these rules as the UI contract:

1. **Action before analysis.** The first screenful should answer "what needs attention?" and "what can I safely do?" before showing exploratory analytics.
2. **One dominant surface per view.** A page may have many panels, but only one should read as the primary focal surface.
3. **Neutral by default.** Accent color, glow, gradients, and heavy borders are reserved for status, selection, or genuinely primary metrics.
4. **Progressive disclosure.** Advanced filters, model controls, scanners, source evidence, and maintenance actions should not compete with normal tasks.
5. **Plain-language labels.** UI copy must describe user outcomes, not internal implementation concepts.
6. **Dense data, quiet chrome.** Tables/charts may be information-dense; surrounding cards, headers, and controls should become visually quieter.
7. **Readable type.** Body copy must not use monospace as the default reading face. Monospace remains appropriate for data-like identifiers, code, and intentionally technical labels.
8. **Mobile preserves priority, not desktop geometry.** Important actions remain first; secondary controls collapse rather than simply wrapping into a wall of buttons.

Create `docs/frontend/PRODUCT_UI_HIERARCHY.md` containing these rules and the resulting component usage guidance.

## Confirmed current state

### Duplicate horizontal containment

`frontend/src/components/layout/AppLayout.vue` already applies:

```text
mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8
```

`frontend/src/components/layout/BasePageLayout.vue` applies another max-width and horizontal gutter. This creates unnecessary nested containment and reduces usable width.

### Page headers have the same visual weight as content cards

`frontend/src/components/ui/PageHeader.vue` wraps every page title in `<Card class="p-6 ...">`. This makes page identity read like another dashboard widget rather than the top of the hierarchy.

### Body typography is monospaced

`frontend/src/assets/css/theme.css` defines `--font-sans` as IBM Plex Mono / monospace, and `main.css` applies it to `body`. This is attractive as a motif but materially raises reading effort in long labels, descriptions, forms, and dense tables.

### Navigation treats all destinations equally

`frontend/src/components/layout/Navbar.vue` presents six equal-weight links plus the theme toggle, while `/settings` exists but has no persistent affordance. The layout wraps on narrow screens and can become visually noisy.

### Visual emphasis is overavailable

`frontend/src/assets/css/main.css` contains several overlapping surface/control systems: `.card`, `.ui-card`, `.ui-panel`, `.glass`, accent gradients, angular chart shells, glows, and page-local card classes. Later packets need a smaller set of hierarchy roles.

## Required changes

### 1. Fix shell ownership of page width

Files:

- `frontend/src/components/layout/AppLayout.vue`
- `frontend/src/components/layout/BasePageLayout.vue`
- `docs/frontend/PageLayout.md`

Make `AppLayout` the single owner of global max width and horizontal gutters. `BasePageLayout` should own vertical spacing and view-local flow, not add a second global gutter/max-width layer.

Preserve an explicit opt-out/expansion mechanism only if an existing view truly needs it.

### 2. Reauthor PageHeader as page identity, not a card

File:

- `frontend/src/components/ui/PageHeader.vue`

Target:

- unboxed title/subtitle region;
- compact optional icon;
- actions aligned to the right on wide screens and below the title on narrow screens;
- quieter subtitle;
- no default glass/card shadow;
- predictable bottom spacing.

Do not remove the current slots or icon prop.

### 3. Establish readable typography roles

Files:

- `frontend/src/assets/css/theme.css`
- `frontend/src/assets/css/main.css`

Use a readable UI sans/system stack for `--font-sans`. Keep `--font-display` / a new `--font-data` as the technical/monospace accent. Headings may retain restrained technical character, but body paragraphs, form labels, navigation, descriptions, and table content should use the readable UI face.

Reduce broad uppercase + high letter-spacing usage. Reserve it for small eyebrow/status labels.

Do not add another remote font dependency.

### 4. Define semantic surface hierarchy

Files:

- `frontend/src/assets/css/theme.css`
- `frontend/src/assets/css/main.css`
- `frontend/src/components/ui/Card.vue`
- `frontend/src/components/base/BasePanel.vue` where needed

Add/reuse semantic roles sufficient for:

- primary/emphasis panel;
- normal panel;
- quiet/utility panel;
- status/attention treatment.

Prefer neutral surfaces and subtle depth. Keep strong gradients/glow for exceptional emphasis only.

Do not perform a repo-wide class migration in this packet. Provide stable primitives/tokens for later packets.

### 5. Calm and complete the app navigation

Files:

- `frontend/src/components/layout/Navbar.vue`
- `frontend/src/App.vue`
- `frontend/src/router/index.js` only if route metadata helps avoid duplicated nav definitions

Requirements:

- use shorter label `Forecast`, not `Forecasting`;
- preserve direct access to Dashboard, Accounts, Transactions, Forecast, Planning, Investments;
- add a low-emphasis Settings affordance without giving it equal visual weight to primary financial destinations;
- prevent mobile navigation from becoming an uncontrolled wrap;
- active route remains obvious without glow-heavy treatment;
- theme control remains accessible but visually secondary.

Do not redesign route URLs in this packet.

### 6. Add regression coverage

Update/add focused tests for:

- `frontend/src/components/layout/__tests__/Navbar.spec.js`
- `frontend/src/components/ui/__tests__/PageHeader.spec.ts`
- a focused AppLayout/BasePageLayout test if no current coverage exists.

Assert structure, navigation access, active state, and mobile-safe semantics. Do not assert brittle pixel values.

## Non-goals

- Do not recompose Dashboard, Accounts, Transactions, Forecast, Planning, or Investments content yet.
- Do not replace Nightfox/Everforest palettes.
- Do not create a new component library.
- Do not remove existing routes.
- Do not use color alone to convey status.

## Implementation order

1. Add the product hierarchy doc.
2. Fix AppLayout/BasePageLayout containment.
3. Reauthor PageHeader.
4. Establish readable typography and semantic surface tokens.
5. Calm Navbar and expose Settings.
6. Update docs/tests.
7. Run frontend validation.

## Acceptance criteria

- [ ] Global page content no longer receives duplicate max-width/gutter wrappers.
- [ ] PageHeader is visually distinct from content cards.
- [ ] Default body text uses a readable UI sans/system stack.
- [ ] Monospace remains available as a deliberate display/data accent.
- [ ] Semantic primary/normal/quiet/attention surface roles are documented and reusable.
- [ ] Primary navigation does not uncontrolled-wrap on narrow screens.
- [ ] Settings is persistently reachable but visually secondary.
- [ ] Existing route destinations remain available.
- [ ] Navbar and PageHeader focused tests pass.
- [ ] No feature-level data behavior changes.

## Validation

```bash
cd frontend
npm run test -- --run
npm run lint
npm run build
```

## Completion report

Report files changed, hierarchy tokens/components added, typography decision, shell width ownership, nav behavior at desktop/mobile widths, tests, and deviations.
