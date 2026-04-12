# Elevation vs Border Contrast (Dashboard Surfaces)

## Purpose

This note defines when dashboard surfaces should use **elevation** (`box-shadow`) versus **edge contrast** (1px/2px framed borders) so styling stays consistent as components evolve.

## Baseline tokens

Use the shared depth and frame tokens from `frontend/src/styles/theme.css`:

- Shadows: `--depth-shadow-resting`, `--depth-shadow-raised`, `--depth-shadow-overlay`
- Interior highlight: `--depth-inner-glow`
- Edge contrast: `--edge-contrast-1`, `--edge-contrast-2`
- Accent edge contrast: `--edge-contrast-accent-cyan`, `--edge-contrast-accent-green`
- Panel geometry rhythm: `--panel-radius-tight`, `--panel-radius-roomy`, `--panel-space-1/2/3`

## Decision rule

### Prefer border contrast first

Use edge contrast as the default framing for:

- dashboard cards and table wrappers,
- filter/control shells inside cards,
- long-lived panels that should feel stable rather than floating.

Apply:

- `1px` border with `--edge-contrast-1` for standard shells,
- `2px` border with accent contrast token for primary/hero surfaces.

### Add elevation only when hierarchy needs separation

Use restrained shadows only when a surface must read as visually higher than neighboring content:

- `--depth-shadow-resting` for standard panel lift,
- `--depth-shadow-raised` for hero or emphasized summary surfaces,
- `--depth-shadow-overlay` for true overlays and modal-like layers.

Always pair depth with `--depth-inner-glow` for subtle interior definition.

## Practical guidance

1. Start with border contrast and spacing tokens.
2. Add the smallest shadow tier that solves legibility/stacking.
3. Avoid mixing heavy gradients plus large shadows on the same shell.
4. Keep corners tight (`--panel-radius-tight` or `--panel-radius-roomy`) and spacing on the 1rem/1.25rem/1.5rem rhythm.

## Scope for this policy

These rules specifically anchor dashboard surfaces, including net overview shells and table wrappers. If a new screen needs a different visual hierarchy, add a follow-up devnote before introducing new depth patterns.
