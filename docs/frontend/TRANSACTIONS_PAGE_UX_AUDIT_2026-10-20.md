# Transactions Page UX Audit (TP-20261020-002)

Date: 2026-10-22 (packet authored 2026-10-20). Scope: scrolling, ledger hierarchy and primary navigation.

## Starting state
Commits `668a4d684` (scroll/nav CSS repair) and `323da107a` (quiet insights, single ledger surface) had
already landed. This packet verified them in a real browser and finished the remaining ledger polish
rather than re-applying them.

## Decisions
| Area | Decision |
|---|---|
| Ledger rows | Removed the `MIN_ROW_COUNT=12` empty padded rows. Short results now render only real rows; loading still uses `SkeletonCard`, and virtualization (>80 rows) is unchanged. |
| Ledger a11y | Scroll region keeps its `Transactions table` label and gains an `aria-describedby` hint that more columns scroll horizontally. `aria-sort` and the row-count caption are unchanged. |
| Scroll chaining | No `overscroll-behavior-y: contain`, no `wheel.prevent`. Verified natively (below). |
| Navbar | Single nowrap scroller at <=1100px with edge fades, auto-reveal of the active route and `aria-current` from the router. No "More" menu: all six routes, Settings and theme fit or scroll in one row at every tested width. |
| Insights / toolbar / filters | Already unboxed and quiet from `323da107a`; filter ownership and backend summaries untouched. No finance calculation changes. |

## Evidence (real browser, Cypress Electron)
`frontend/cypress/e2e/transactions-scroll-nav.cy.js` dispatches wheel input through
`Input.dispatchMouseEvent` (CDP), so the browser's own scroll chaining decides the result.

- Short 10-row table: wheel over the grid scrolls the document (scrollY increases).
- 120-row virtualized table: wheel scrolls the inner region first with the page unmoved; once the
  inner region is at its end, further wheel scrolls the page.
- Navbar at 320, 390, 640, 768, 950, 1100, 1280px: all links share one row, the active route lies
  inside the scroller, and the document has no horizontal overflow. Screenshots are written to
  `frontend/cypress/screenshots/transactions-scroll-nav.cy.js/transactions-nav-<width>.png` (git-ignored).

## Not run / limits
- Touch, trackpad inertia, keyboard PageDown and Shift-wheel were not exercised natively; only mouse wheel.
- Screenshots are viewport captures of the nav at each width, not a before/after pair of the whole page.
- Edit, transfer and recurring handoff are covered by existing unit specs, not re-driven in the browser.
