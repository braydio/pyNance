# Nightfox Dark Theming Guide

This document describes how to configure and extend the frontend theme for _pyNance_.
The project now uses the [Nightfox](https://github.com/EdenEast/nightfox.nvim) dark palette as the sole theme.
It introduces a modular approach built around CSS custom properties.

## Directory Layout

```
frontend/
└─ src/
   ├─ assets/
   │  └─ css/
   │     └─ main.css          # global Tailwind + base styles
   └─ styles/
      ├─ theme.css           # Nightfox palette
      └─ global-colors.css   # project-wide aliases
```

- `theme.css` defines the canonical Nightfox color palette.
- `global-colors.css` re-exports the palette variables and adds a few aliases
  used throughout components.

## Updating the Theme

Customize colors directly in `theme.css`. Keep variable names consistent so
components continue to work.

## Variable Reference

Below are the most common tokens used across the UI. Each theme should define
all of them:

| Variable                                        | Usage                             |
| ----------------------------------------------- | --------------------------------- |
| `--page-bg`                                     | overall page background           |
| `--color-bg`                                    | container backgrounds             |
| `--color-bg-secondary`                          | secondary surfaces                |
| `--themed-bg`                                   | translucent frosted panels        |
| `--themed-border`                               | subtle borders for frosted panels |
| `--surface`                                     | card backgrounds                  |
| `--divider`                                     | table/grid lines                  |
| `--input-bg`                                    | form inputs                       |
| `--theme-fg`                                    | default foreground text           |
| `--color-text-muted`                            | subdued text                      |
| `--color-accent-cyan` / `--color-accent-purple` | accent colors                     |
| `--color-accent-yellow`                         | secondary accent                  |
| `--color-accent-blue`                           | informational accent              |
| `--color-accent-red`                            | danger or expense accent          |
| `--color-accent-green`                          | positive/earning accent           |
| `--color-accent-orange`                         | warning or trend accent           |
| `--color-accent-indigo`                         | fresh highlight accent            |
| `--primary` / `--primary-dark`                  | generic button colors             |
| `--hover-bg`                                    | hover background for buttons      |
| `--hover-glow`                                  | drop shadow for hover effects     |
| `--color-success` / `--color-bg-success`        | success states                    |
| `--color-error` / `--color-bg-error`            | error states                      |
| `--color-warning` / `--color-bg-warning`        | warning states                    |
| `--color-info` / `--color-bg-info`              | informational states              |

Additional variables such as `--color-accent-magenta`, `--color-accent-indigo`,
`--bar-gradient-end`, `--asset-gradient-start`/`--asset-gradient-end`, and
`--liability-gradient-start`/`--liability-gradient-end` are used by specific
charts and widgets. Review the default theme for the full list.

## How the Theme Loads

`main.css` imports `global-colors.css` before Tailwind base layers. This ensures
variables are available everywhere, including in component scoped styles.

```css
@import "../../styles/global-colors.css";
@tailwind base;
```

When the application starts, the browser loads `main.css` which in turn loads the
active theme. Swapping themes at runtime can be achieved by dynamically
injecting a `<link>` to another theme file or by replacing the `href` of the
existing link.

## Frosted Glass Effect

The Nightfox theme uses semi-transparent backgrounds (`--themed-bg`) and subtle
borders (`--themed-border`) to create a frosted glass look. Components can apply
these styles using `backdrop-filter: blur(6px)` or by setting the background and
border variables directly.

## Data table surface hierarchy

Data tables prioritize neutral, token-driven surfaces so hero metrics and gradient cards retain visual focus.

- Wrap tables with the `table-panel` + `table-shell` container classes to pick up the neutral table tokens: `var(--table-surface-strong)` shells, `var(--table-surface)` bodies, and `var(--table-border)` outlines.
- Table headers use `var(--table-header)` while zebra rows alternate between `var(--table-surface)` and `var(--table-surface-alt)`; hover states rely on `var(--table-hover)`.
- Filters and inline controls should reuse `var(--table-control)` to stay neutral and avoid drawing focus away from gradient cards.
- Accent colors remain on chips and badges, but gradient fills are reserved for hero metrics and summary cards.
- Use `--color-accent-indigo` for “active edit” or “fresh highlight” states when you need a distinct, non-critical accent.
- Reference implementations live in `frontend/src/components/tables/AccountsTable.vue`, `frontend/src/components/tables/TransactionsTable.vue`, and the modal/inline tables in `frontend/src/components/tables/UpdateTransactionsTable.vue` and `ModalTransactionsDisplay.vue`.

## Accounts page surface hierarchy example

Use the Accounts page as the baseline pattern for preventing accent overuse:

- **Primary emphasis only**: apply a restrained gradient overlay on the top KPI/overview card (`Net Change Summary`) and keep the base as `var(--themed-bg)` with a themed border.
- **Secondary panels**: history and activity panels should use `var(--themed-bg)` + `var(--themed-border)` with no gradient fill.
- **Tertiary utility panels**: analysis/manage cards should use neutral table surfaces (`var(--table-surface-strong)` / `var(--table-surface)` and `var(--table-border)`) so charts and controls do not compete with KPI emphasis.
- **Tables and dense controls**: continue using `table-panel` and `table-shell` tokenized surfaces for visual consistency.
- **Header separators and rails**: default to neutral border tokens (`var(--themed-border)`) unless the element is part of a primary KPI surface.

### Accounts anti-drift checklist

When shipping Accounts page UI updates, validate these rules in review:

1. No gradient backgrounds on secondary or tertiary cards.
2. No accent-gradient horizontal rules outside primary KPI emphasis.
3. `Net Change Summary` remains the only gradient-emphasis surface in tab content.
4. Headings and spacing follow `frontend/docs/typography-spacing-guide.md` scales and spacing tokens.

This hierarchy keeps accents purposeful: gradients communicate primary KPI focus, while secondary and tertiary surfaces remain calm and readable.

## Conclusion

This guide establishes a foundation for consistent theming. By defining all
colors and common surfaces in a dedicated theme file, future designs can be
implemented simply by creating additional theme files and adjusting the import in
`global-colors.css`.
