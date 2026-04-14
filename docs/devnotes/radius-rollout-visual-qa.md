# Radius/Depth Rollout Visual QA Checklist

Use this checklist when reviewing any phase in `docs/frontend/radius-rollout-phases.md`.

## Capture protocol

For each impacted route in the active phase:

1. Capture one **before** screenshot from the base branch (or prior release commit).
2. Capture one **after** screenshot from the proposed changes.
3. Use the same viewport per route (desktop and/or mobile) and note viewport dimensions in PR notes.
4. Include interaction captures when relevant (hover/focus/modal-open states).

## Required QA checklist

Mark each item pass/fail and include notes for failures:

### 1) Corner usage

- [ ] Surfaces use approved radius tokens from `theme.css` and helper classes.
- [ ] `rounded-full` appears only for semantic circles (avatars/status dots).
- [ ] No arbitrary `rounded-*` utility appears without documented justification.

### 2) Border contrast

- [ ] Panel borders use approved edge-contrast tokens.
- [ ] Hero/accent surfaces use approved stronger border tokens only where intended.
- [ ] Border contrast is still distinguishable against adjacent surfaces.

### 3) Spacing rhythm

- [ ] Internal panel spacing follows the shared panel spacing rhythm.
- [ ] Adjacent section spacing is consistent across sibling surfaces.
- [ ] Dense controls maintain consistent vertical rhythm.

### 4) Focus visibility

- [ ] Keyboard focus indicators are visible on all interactive controls.
- [ ] Focus rings are not clipped by parent overflow or radius settings.
- [ ] Focus styles remain distinct against both base and elevated surfaces.

## Review output template

Use this block in PR descriptions:

```md
## Radius/Depth Visual QA

### Screenshots
- Route: `<route>`
  - Before: `<image/link>`
  - After: `<image/link>`
  - Viewport: `<width>x<height>`

### Checklist
- Corner usage: Pass/Fail - `<notes>`
- Border contrast: Pass/Fail - `<notes>`
- Spacing rhythm: Pass/Fail - `<notes>`
- Focus visibility: Pass/Fail - `<notes>`
```
