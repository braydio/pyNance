# Account Balance History Delivery Roadmap

## Scope

Deliver a production-ready account balance history capability that is reliable across historical ranges, cache-aware at scale, and safe to consume from both API clients and the Accounts UI.

### In scope

- Revalidate historical balance derivation rules in the backend service layer.
- Normalize cache read/write and invalidation behavior for account history windows.
- Stabilize and document API request/response contracts for balance history endpoints.
- Integrate history ranges and rendering states into the Accounts UI flow.
- Add resiliency safeguards (fallbacks, retries, degraded modes) for partial failures.
- Improve performance for warm and cold history reads under realistic account sizes.

### Out of scope

- New visual redesign of charts or account page layout.
- Multi-currency conversion features beyond existing currency display assumptions.
- Changes to Plaid product onboarding flows unrelated to account history.

## Success criteria

- Daily balances are reproducible for the same account/date window across repeated runs.
- Cache hit behavior is observable and meets agreed thresholds for common windows.
- API contract is version-safe, documented, and covered by backend contract tests.
- Frontend range controls and chart states handle loading, empty, and error paths.
- Existing `AccountHistory` rows are migrated/backfilled without data loss.
- Monitoring and release checklists are completed before general rollout.

## Phased delivery plan

### Phase 1: Data correctness

- Confirm source-of-truth logic for deriving balances from transactions, opening snapshots, and balance deltas.
- Add deterministic fixture-driven tests for sparse histories, reversals, and same-day multi-transaction ordering.
- Document edge-case behavior (empty windows, closed accounts, missing transaction dates).

**Exit criteria**

- Golden test fixtures pass for all target edge cases.
- Manual SQL spot checks match service output for sampled accounts.

### Phase 2: Cache behavior

- Define cache key granularity (account, date window, currency context).
- Implement explicit invalidation triggers for transaction imports, account edits, and refresh jobs.
- Add cache telemetry for hits, misses, stale serves, and recompute duration.

**Exit criteria**

- Cache invalidation matrix documented and validated in tests.
- Metrics show predictable warm-cache improvement over cold-cache baselines.

### Phase 3: API contract

- Lock request query parameters for date bounds and optional aggregation modes.
- Validate response payload schema (ordering, numeric precision, metadata fields).
- Add negative-path handling for malformed date ranges and unknown accounts.

**Exit criteria**

- Route-level contract tests cover success and error envelopes.
- API reference/docs updated with examples and field semantics.

### Phase 4: UI integration

- Wire frontend API client methods for selectable windows and refresh handling.
- Ensure chart/table consumers normalize chronological ordering and timezone assumptions.
- Support empty/error/retry states that preserve current page usability.

**Exit criteria**

- Component/unit tests cover range switching and state transitions.
- Manual smoke test confirms parity with backend payloads.

### Phase 5: Resiliency

- Add guarded fallback behavior when history recomputation fails (last known good snapshot + warning).
- Ensure background backfills are resumable and idempotent.
- Introduce structured logging with correlation IDs for history requests.

**Exit criteria**

- Failure-injection tests verify graceful degradation.
- Operational runbook includes triage and rollback steps.

### Phase 6: Performance

- Benchmark hot paths for 30-day, 90-day, 365-day, and full-history windows.
- Reduce expensive recomputations through bounded batching and selective hydration.
- Set and validate latency/error SLO targets for history endpoints.

**Exit criteria**

- Agreed p95 latency thresholds met in staging-like datasets.
- Performance regressions have alert thresholds and owner response procedures.

## Ownership by area

| Area | Primary owners | Responsibilities |
| --- | --- | --- |
| Backend | API + data services maintainers | Derivation logic, cache semantics, migrations, contract enforcement |
| Frontend | Accounts UI maintainers | Range UX, rendering states, client normalization, user-facing resilience |
| Tests | QA + feature maintainers | Unit/integration/contract/performance coverage and regression gates |
| Docs | Feature lead + code owners | Roadmaps, API docs, service docs, runbooks, release notes |

## Migration/backfill plan for existing `AccountHistory`

1. **Audit current records**
   - Snapshot row counts, date coverage per account, and null/duplicate anomalies.
   - Export pre-migration verification report for rollback comparison.
2. **Schema and index readiness**
   - Confirm required constraints and supporting indexes exist before backfill jobs.
   - Apply migration in a low-traffic window and validate with `flask db upgrade` checks.
3. **Incremental backfill execution**
   - Recompute in deterministic batches by account and bounded date windows.
   - Track checkpoints so jobs can resume from last successful account/date cursor.
4. **Dual-read validation window**
   - Temporarily compare newly recomputed results against legacy reads for sampled accounts.
   - Flag divergence over agreed tolerance and halt rollout if threshold is exceeded.
5. **Cutover and cleanup**
   - Switch primary reads to refreshed `AccountHistory` dataset once validation passes.
   - Remove temporary verification artifacts and close migration tasks with signed checklist.

## Observability and regression checklist

- Metrics emitted:
  - request count/rate by endpoint and status code,
  - cache hit/miss/stale counters,
  - recompute duration histogram,
  - backfill throughput and failure counters.
- Logging:
  - structured logs with account ID, date window, cache mode, correlation/request ID,
  - explicit error taxonomy for validation vs dependency vs persistence failures.
- Alerting:
  - p95 latency breach,
  - error-rate spike,
  - sustained cache-miss anomalies,
  - stalled backfill cursor.
- Regression checks:
  - backend unit and route contract tests,
  - frontend state/rendering tests for success/empty/error,
  - migration verification queries and sampled account parity checks.

## Release validation checklist

- [ ] All roadmap phase exit criteria met or deferred with documented risk acceptance.
- [ ] Backend tests, frontend tests, and lint/format checks pass in CI.
- [ ] Migration/backfill dry run completed with parity report attached.
- [ ] Observability dashboards and alerts deployed and verified in staging.
- [ ] API and docs updates linked from roadmap and index pages.
- [ ] Rollout plan includes staged enablement, rollback trigger, and owner on-call coverage.
- [ ] Post-release validation confirms expected latency, error rate, and cache-hit targets.

_Last updated: 2026-03-04_
