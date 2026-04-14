# Corner Radius Migration Guide

## Purpose

This guide defines the allowed corner usage for frontend component categories so the dashboard stays consistent with the angular visual system.

## Radius tokens

Defined in `frontend/src/styles/theme.css`:

- `--radius-0`: no rounding (hard edge)
- `--radius-1`: compact chip/input radius
- `--radius-2`: standard interactive control radius
- `--radius-3`: large surface radius for major cards/panels

## Allowed corner usage by component type

| Component type                                                   | Allowed token(s)             | Notes                                                                            |
| ---------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------------- |
| Page/section wrappers, hero cards, dashboard panels              | `--radius-3`                 | Use for prominent, high-visibility surfaces only.                                |
| Cards and table containers                                       | `--radius-2` to `--radius-3` | Prefer `--radius-3` for dashboard hero surfaces, `--radius-2` for nested shells. |
| Buttons, selects, form controls                                  | `--radius-1` to `--radius-2` | Primary buttons typically use `--radius-2`; dense controls can use `--radius-1`. |
| Chips, filter tags, decorative pills                             | `--radius-1`                 | Do not use fully rounded pills for decorative tags.                              |
| Hard-edge elements (dividers, bars, strict rectangular surfaces) | `--radius-0`                 | Explicit no-rounding token for angular edges.                                    |
| Semantic circles (avatars, status dots, presence indicators)     | Circle (`rounded-full`)      | Keep circular treatment only when meaning requires a circle.                     |

## Migration checklist

1. Replace Tailwind `rounded-*` classes on shared/global classes with token-backed radius values.
2. Prefer `.ui-radius-*` helpers from `frontend/src/assets/css/main.css` in templates.
3. Keep `rounded-full` only for semantic circles; convert decorative pills to `--radius-1`.
4. During review, verify new components do not introduce larger radii outside this scale.

## Rollout governance

For phased delivery expectations and route-level capture requirements, follow:

- `docs/frontend/radius-rollout-phases.md`
- `docs/devnotes/radius-rollout-visual-qa.md`

Any PR changing frontend surface geometry should include the visual QA template and before/after captures.

