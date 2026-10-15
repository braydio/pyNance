# TP-20261014-010: Theme Contrast and Typography

**Packet ID:** TP-20261014-010  
**Status:** Ready  
**Created:** 2026-10-14  
**Last updated:** 2026-10-14  
**Repository:** braydio/pyNance  
**Target branch:** main  
**Canonical path:** docs/task-packets/active/TP-20261014-010-theme-contrast-typography.md  
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
