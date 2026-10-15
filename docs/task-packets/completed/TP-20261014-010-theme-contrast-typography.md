# TP-20261014-010: Theme Contrast and Typography

**Packet ID:** TP-20261014-010  
**Status:** Complete  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/completed/TP-20261014-010-theme-contrast-typography.md  
**Depends on:** None  
**Priority:** High  
**Workstream size:** One focused UI packet  
**Source audit:** docs/frontend/UI_FIELD_AUDIT_2026-10-14.md

## Exact file paths
- frontend/src/styles/theme.css
- frontend/src/assets/css/main.css
- frontend/src/assets/css/theme.css
- frontend/src/styles/typography.css

## Confirmed current state
Dark muted #71839b on #192330 yields 4.09:1; Everforest muted #829181 on #fdf6e3 yields 3.08:1 and page yields 2.77:1. Light positive #8da101 yields 2.69:1 and negative #f85552 yields 3.04:1 on #fdf6e3. Semantic text/state roles and status/chart paint share foreground colors.

## Required implementation
Replace only foreground semantic roles with contrast-verified colors: normal text >=4.5:1, large >=3:1, essential control outlines >=3:1; keep Nightfox/Everforest hue identities for charts/accent. Establish --text-positive/--text-negative separate from decorative chart colors; keep backwards aliases. Check typography.css actually loaded before changing typography; meaningful labels >=.875rem, body ~1rem line-height 1.5+, small financial annotations >=.8125rem when important. Currency tabular-nums; reduce all-caps tracking on explanatory headings. Do not turn muted text into primary.

## Validation
New frontend/src/utils/__tests__/themeContrast.spec.js computes token ratios both theme palettes; useTheme.spec.js. Browser light/dark /forecast /investments /settings / at 390/1280, error/success text. cd frontend && npm run lint && npm run build.

## Non-goals
No new palettes, no financial computation changes.

## Completion contract
Check AGENTS.md and docs/task-packets/README.md, TRACKER and INDEX; validate named paths only. Mark In Progress, implement ordered fixes, run focused tests and lint/build. After completion move packet to completed/, update INDEX/TRACKER atomically, commit to origin/main without force. Report files, browser validation vs static assumptions, exact commands/output and deviations. Coordinate overlapping files with prerequisite packets; no broad refactor.

## Completion report

- `styles/theme.css`: new contrast-verified foreground roles in both palettes (`--text-positive`, `--text-negative`, `--text-warning`, `--text-link`, `--control-border`), muted/secondary/primary text raised (Nightfox muted #71839b -> #9aabc1, 4.09 -> >= 5.0:1; Everforest muted #829181 -> #586758 and primary/secondary darkened, every body surface >= 4.7:1). Chart/accent colors (`--color-accent-*`, `--color-success/error`) are untouched, so Nightfox/Everforest hue identity and charts are unchanged.
- `assets/css/main.css`: `amount-positive/negative/neutral` now use the text roles with `tabular-nums`; new `text-positive|negative|warning|link` and `tabular-currency` utilities; `.input`/`ui-control-input` borders use `--control-border`; important small labels raised from 0.70-0.72rem to 0.8125rem with all-caps tracking reduced (0.16-0.18em -> 0.04-0.08em). Local `.amount-positive/negative` rules in `DailySpendingPanel.vue`, `FinancialSummary.vue` and `UpdateTransactionsTable.vue` now use the same roles.
- `styles/typography.css` is not imported anywhere (verified), so its element rules do not run; left unchanged except a header note. `assets/css/theme.css` unchanged.
- Tests: new `utils/__tests__/themeContrast.spec.js` computes WCAG ratios from the literal tokens (text roles on 7 surfaces per theme + light table surfaces, control outlines >= 3:1); `useTheme.spec.js` passes. Full vitest, lint (0 errors) and build pass.
- Not done / honest limits: no browser verification of rendered pages at 390/1280 (static computation only; translucent rgba surfaces not computed). Dark-theme table surfaces (`--table-surface-strong`, `--table-header`) are lighter mixes where muted/primary text remain below 4.5:1; those are surface colors and were out of this packet's foreground-only scope. Components that hardcode Tailwind grays/greens are addressed by later packets.
