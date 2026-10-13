# Product UI Hierarchy

The UI contract for pyNance views (TP-20261007-002). Later view packets reuse these rules and primitives instead of inventing page-local styling.

## Rules

1. **Action before analysis.** The first screenful answers "what needs attention?" and "what can I safely do?" before exploratory analytics.
2. **One dominant surface per view.** Many panels are fine; only one reads as the focal surface.
3. **Neutral by default.** Accent color, glow, gradients and heavy borders are reserved for status, selection or genuinely primary metrics.
4. **Progressive disclosure.** Advanced filters, model controls, scanners, source evidence and maintenance actions must not compete with normal tasks.
5. **Plain-language labels.** Copy describes user outcomes, not internal concepts.
6. **Dense data, quiet chrome.** Tables and charts may be dense; surrounding cards, headers and controls stay quiet.
7. **Readable type.** Body copy is not monospace. Monospace is for data-like identifiers, code and deliberately technical labels.
8. **Mobile preserves priority, not desktop geometry.** Important actions stay first; secondary controls collapse.

## Component usage

- **Width/gutters:** `AppLayout` owns the global `max-w-7xl` and `px-4 sm:px-6 lg:px-8`. `BasePageLayout` only adds vertical padding (`py-6`) and gap.
- **`PageHeader`:** unboxed page identity (title, quiet subtitle, optional small icon, actions right on wide screens / below on narrow). Never a card.
- **Typography:** `--font-sans` is a system sans stack for body, labels, nav, forms and tables. `--font-display` (headings/technical accents) and `--font-data` (IDs, figures that benefit from mono) are the monospace faces. Use uppercase + wide tracking only for small eyebrow/status labels.
- **Surface roles** (`main.css`):

  | Class | Use |
  | --- | --- |
  | `.surface-primary` | The single dominant panel of a view |
  | `.surface-normal` | Default content panel |
  | `.surface-quiet` | Utility/secondary panel, no fill |
  | `.surface-attention` | Needs-attention state; always pair with text/icon, never color alone |

  `Card` (`.card .glass`) remains for existing consumers; migrate to the roles per view packet, not wholesale.
- **Navigation:** six primary destinations (Dashboard, Accounts, Transactions, Forecast, Planning, Investments) scroll horizontally on narrow screens rather than wrapping; Settings and the theme toggle are low-emphasis and collapse to icons on mobile.
