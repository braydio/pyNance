# Daily Net Chart Guidelines

**Purpose.** The Daily Net chart in `DailyNetChart.vue` tracks three interrelated metrics for each date: gross income, gross expenses, and the net delta. It lives on the dashboard and drives `FinancialSummary` data via emitted events.

**Visual rules.**

- **Stacked bars.** Expenses render as the red column extending downward from 0, income renders as the green column starting at 0 and building upward. Both bars share the same stack (`daily-stack`) so they visually align on the same x-axis tick.
- **Net indicator.** Net is not a bar. It is a transparent line dataset with `netIndicator` metadata. `netLinePlugin` uses that dataset solely to draw the horizontal yellow dash on each column, keeping the net bar from overlapping the stacked columns. This dash should stay visible in front of the bars.
- **Prior-period overlay.** The comparison overlay line uses a light grey/white stroke (`--color-text-light` or `#f8fafc`) to stay visible against the dark card without clashing with the yellow net line.
- **Trendline colors.** Moving-average lines rely on the purple (`--color-accent-purple`) and cyan (`--color-accent-cyan`) accents for the 7-day and 30-day averages, while the flat average income/expense lines match the green/red bar colors and render with a subtle dashed stroke so they stay visually tied to the daily stacks. These trendlines should remain thin, transparent-filled strokes with no visible points.
- **Scaling.** The y-axis is configured with `stacked: true` so the bars grow from zero in appropriate directions. Do not convert expenses to positive values or change the axis stacking without a clear reason.
- **Density tuning.** Bar width, spacing, and x-axis tick density are derived from the number of labels in view. Short ranges keep wider bars with day labels, medium ranges tighten spacing, and long ranges switch to slimmer bars with month-only labels to preserve readability.
- **Tooltip.** The hover tooltip uses the same treatment as the categories chart: theme card background (`--theme-bg`), yellow outline (`--color-accent-yellow`), and `Fira Code`-style typography for title/body. It lists Income, Expenses, Net, and Transaction count, plus the “Prior …” block when the comparison overlay is active, and the card now snaps to the yellow net dash.
- **Tooltip pointer.** Tooltips now snap to the yellow net dash using a custom `positioner` so the arrow always points at the net indicator, creating a tighter visual relationship between the hover card and the metric.
- **Legend.** The default Chart.js legend is hidden (`display: false`) to keep the card clean.

**Why it matters.** The combination of stacked income/expense bars with a front-facing net line supports the “what you earned vs what you spent vs what you kept” story we want everywhere, while the consistent tooltip and absence of redundant legend keeps the card uncluttered.

**Change control.** This section defines the baseline. Any future tweaks to stacking behavior, colors, tooltip tone, or legend visibility should be made only with explicit product or design direction so the chart remains consistent with the documented intent.
