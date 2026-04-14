## Summary

- Describe what changed and why.
- List impacted areas (backend/frontend/tests/docs).

## Validation

- [ ] `pytest -q`
- [ ] `pre-commit run --all-files`
- [ ] Frontend checks run (`npm run lint`, plus targeted UI tests as needed)

## Radius/Depth Visual QA (required for frontend surface changes)

### Screenshots (before/after)

- Route: `<route>`
  - Before: `<image/link>`
  - After: `<image/link>`
  - Viewport: `<width>x<height>`

### Checklist

- [ ] Corner usage reviewed (token scale only; semantic `rounded-full` exceptions only)
- [ ] Border contrast reviewed (approved edge/depth tokens)
- [ ] Spacing rhythm reviewed (panel spacing rhythm maintained)
- [ ] Focus visibility reviewed (keyboard focus remains visible and unclipped)

## Rounded utility review gate

- [ ] I did not introduce new arbitrary `rounded-*` classes.
- [ ] If I introduced `rounded-*`, I documented business/UX justification and follow-up cleanup task.
- [ ] I confirmed existing radius helpers/tokens could not satisfy the requirement before using any exception.

## Documentation

- [ ] Updated docs in `docs/frontend/` when frontend behavior/patterns changed.
- [ ] Updated docs in `docs/devnotes/` with implementation notes and QA rationale.
- [ ] Updated `docs/index/INDEX.md` for any new docs pages.
