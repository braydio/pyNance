# Nightfox Dark Theming Guide

This document describes how to configure and extend the frontend theme for *pyNance*.
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
      ├─ global-colors.css   # imports the active theme
      └─ themes/
         └─ nightfox.css     # Nightfox palette
```

* `global-colors.css` defines the variables that components rely on. It imports
  a theme file so new themes can be swapped without editing components.
* `themes/nightfox.css` is the official theme based on the Nightfox palette.

## Adding a New Theme

1. Create a file in `frontend/src/styles/themes/` with the same variable names
   as `nightfox.css`.
2. Replace the `@import` line at the top of `global-colors.css` to point to the
   new theme file or dynamically inject the file at runtime.
3. Keep variable names consistent so existing components continue to work.

A minimal theme file looks like this:

```css
/* example: themes/solarized-light.css */
:root {
  --page-bg: #fdf6e3;
  --surface: #ffffff;
  --theme-fg: #073642;
  /* ...other variables... */
}
```

## Variable Reference

Below are the most common tokens used across the UI. Each theme should define
all of them:

| Variable | Usage |
|----------|-------|
| `--page-bg` | overall page background |
| `--color-bg` | container backgrounds |
| `--color-bg-secondary` | secondary surfaces |
| `--themed-bg` | translucent frosted panels |
| `--themed-border` | subtle borders for frosted panels |
| `--surface` | card backgrounds |
| `--divider` | table/grid lines |
| `--input-bg` | form inputs |
| `--theme-fg` | default foreground text |
| `--color-text-muted` | subdued text |
| `--color-accent-cyan` / `--color-accent-purple` | accent colors |
| `--color-accent-yellow` | secondary accent |
| `--color-accent-blue` | informational accent |
| `--color-accent-red` | danger or expense accent |
| `--color-accent-green` | positive/earning accent |
| `--color-accent-orange` | warning or trend accent |
| `--primary` / `--primary-dark` | generic button colors |
| `--hover-bg` | hover background for buttons |
| `--hover-glow` | drop shadow for hover effects |
| `--color-success` / `--color-bg-success` | success states |
| `--color-error` / `--color-bg-error` | error states |
| `--color-warning` / `--color-bg-warning` | warning states |
| `--color-info` / `--color-bg-info` | informational states |

Additional variables such as `--color-accent-magenta`, `--color-accent-cyan`,
`--bar-gradient-end`, `--asset-gradient-start`/`--asset-gradient-end`, and
`--liability-gradient-start`/`--liability-gradient-end` are used by specific
charts and widgets. Review the default theme for the full list.

## How the Theme Loads

`main.css` imports `global-colors.css` before Tailwind base layers. This ensures
variables are available everywhere, including in component scoped styles.

```css
@import '../../styles/global-colors.css';
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

## Conclusion

This guide establishes a foundation for consistent theming. By defining all
colors and common surfaces in a dedicated theme file, future designs can be
implemented simply by creating additional theme files and adjusting the import in
`global-colors.css`.

