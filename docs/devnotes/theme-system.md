---
Owner: Frontend
Last Updated: 2026-06-12
Status: Active
---

# Frontend Theme System

## Purpose

The frontend supports persistent, client-side visual themes through semantic CSS variables. Themes change color and elevation without changing component structure or requiring a backend request.

## Supported themes

- **Nightfox** (`nightfox`) is the default dark palette.
- **Everforest Light** (`everforest-light`) is a pale green and cream light palette inspired by Everforest's low-contrast approach.

Users can switch themes from the navigation bar or the Appearance section of Settings. The selected identifier is saved in `localStorage` under `pynance-theme` and applied before Vue mounts to minimize theme flashing.

## Architecture

- `frontend/src/composables/useTheme.js` owns supported theme metadata, validation, persistence, and the reactive active-theme state.
- `frontend/src/styles/theme.css` defines default semantic tokens and overrides them under `:root[data-theme='everforest-light']`.
- Components should consume semantic variables such as `--surface-1`, `--text-primary`, `--border-subtle`, and `--accent-primary`; they should not branch on a theme identifier.
- `frontend/src/assets/css/main.css` provides shared site-wide accent marks for standard cards and settings panels.

## Adding a theme

1. Add the theme metadata to `THEMES` in `useTheme.js`.
2. Add a complete semantic-token override in `theme.css` using a `data-theme` selector.
3. Add a palette preview in Settings.
4. Extend `useTheme.spec.js` and visually verify dashboard, transactions, planning, investments, and settings at desktop and mobile widths.

## Accent policy

Accent marks should remain restrained: use short 2px edge marks, active-navigation underlines, and semantic accent tokens. Avoid full-panel saturated borders or gradients that compete with financial data.
