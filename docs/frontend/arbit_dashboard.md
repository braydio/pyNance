# Arbit Dashboard UI

The Arbit dashboard view (`frontend/src/views/ArbitDashboard.vue`) stitches together
status, controls, metrics, alerts, opportunities, trades, and the live RSAssistant
log feed.

## Components

- `ArbitStatus` – polls `/api/arbit/status` to display engine readiness.
- `ArbitControls` – starts/stops the worker and triggers alert evaluations.
- `ArbitMetrics` – renders exporter metrics grouped for quick scanning.
- `ArbitAlerts` – subscribes to `/api/arbit/alerts/stream` for profit alerts.
- `ArbitOpportunities` and `ArbitTrades` – placeholders for surfaced signals and
  recent executions.
- `ArbitLogs` – polls `/api/arbit/logs` for RSAssistant log lines and presents
  them in a themed feed for operators.

## Layout

`ArbitDashboard.vue` arranges the components in stacked card sections to keep the
control plane, analytics, and log feed visible without leaving the page. The log
card uses the same spacing and accent colors as the rest of the dashboard so it
feels native to the experience.
