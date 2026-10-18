<!--
  SafeToSpendCard.vue
  Shows a glanceable daily spend guardrail with horizon controls and rationale.
-->
<template>
  <section class="safe-spend-card" aria-labelledby="safe-spend-title">
    <div class="safe-spend-card__header">
      <div>
        <p class="safe-spend-card__kicker">Daily Decision</p>
        <h2 id="safe-spend-title" class="safe-spend-card__title">Safe to Spend</h2>
      </div>
      <span class="safe-spend-card__status" :class="`safe-spend-card__status--${statusClass}`">
        {{ statusLabel }}
      </span>
    </div>

    <div class="safe-spend-card__modes" aria-label="Safe to spend horizon">
      <button
        v-for="option in modeOptions"
        :key="option.value"
        class="accent-toggle-btn angular-chart-chip safe-spend-card__mode"
        :class="{
          'accent-toggle-btn--active angular-chart-chip--active': selectedMode === option.value,
        }"
        type="button"
        :aria-pressed="selectedMode === option.value"
        @click="emit('update:mode', option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <div v-if="loading" class="safe-spend-card__empty" role="status">Calculating spend room…</div>
    <div v-else-if="error" class="safe-spend-card__empty safe-spend-card__empty--error">
      {{ error }}
    </div>
    <template v-else-if="payload">
      <div class="safe-spend-card__amount-row">
        <span class="safe-spend-card__amount">{{ formatCents(primaryAmount) }}</span>
        <span class="safe-spend-card__amount-copy">Daily allowance</span>
      </div>
      <p class="safe-spend-card__message">{{ payload.message }}</p>
      <p
        v-if="protectedTotal !== null"
        class="safe-spend-card__secondary"
        data-testid="protected-total"
      >
        Total protected spending room: {{ formatCents(protectedTotal) }}
      </p>
      <ul v-if="windowLines.length" class="safe-spend-card__windows" data-testid="windows">
        <li v-for="line in windowLines" :key="line">{{ line }}</li>
      </ul>
      <ul v-if="warnings.length" class="safe-spend-card__warnings" data-testid="warnings">
        <li v-for="warning in warnings" :key="warning">{{ warning }}</li>
      </ul>

      <dl class="safe-spend-card__components">
        <div>
          <dt>Spendable cash</dt>
          <dd>{{ formatCents(payload.components?.spendable_cash_cents) }}</dd>
        </div>
        <div>
          <dt>Upcoming bills</dt>
          <dd>-{{ formatCents(payload.components?.upcoming_outflows_cents) }}</dd>
        </div>
        <div>
          <dt>Protected buffer{{ bufferNote }}</dt>
          <dd>-{{ formatCents(payload.components?.required_buffer_cents) }}</dd>
        </div>
        <div>
          <dt>Spent today (already in balance)</dt>
          <dd>{{ formatCents(payload.components?.spent_today_cents) }}</dd>
        </div>
      </dl>

      <section class="safe-spend-card__reserved" data-testid="reserved">
        <button
          class="safe-spend-card__reserved-toggle"
          type="button"
          aria-controls="safe-spend-reserved-panel"
          :aria-expanded="reservedOpen"
          @click="reservedOpen = !reservedOpen"
        >
          <span>What's reserved?</span>
          <span aria-hidden="true">{{ reservedOpen ? '−' : '+' }}</span>
        </button>
        <p class="safe-spend-card__reserved-summary" data-testid="reserved-summary">
          {{ reservedSummary }}
        </p>
        <div v-show="reservedOpen" id="safe-spend-reserved-panel" data-testid="reserved-panel">
          <div v-for="group in reserveGroups" :key="group.status" class="safe-spend-card__group">
            <h3 class="safe-spend-card__group-title">
              <span>{{ group.label }}</span>
              <span>-{{ formatCents(group.total) }}</span>
            </h3>
            <ul class="safe-spend-card__bills">
              <li v-for="bill in group.rows" :key="bill.id + bill.due_date" data-testid="bill-row">
                <span class="safe-spend-card__bill-name">
                  {{ bill.name }}
                  <small>
                    {{ bill.due_date
                    }}<template v-if="accountName(bill.account_id)">
                      · {{ accountName(bill.account_id) }}</template
                    ><template v-if="bill.estimated"> · estimated</template>
                  </small>
                </span>
                <span class="safe-spend-card__bill-amount"
                  >-{{ formatCents(bill.amount_cents) }}</span
                >
              </li>
            </ul>
          </div>
          <p
            v-if="!reserveGroups.length"
            class="safe-spend-card__secondary"
            data-testid="no-reserved"
          >
            {{ noReservedCopy }}
          </p>
          <p v-if="beyondProtectionCopy" class="safe-spend-card__secondary">
            {{ beyondProtectionCopy }}
          </p>
        </div>
        <div v-if="needsReview.length" class="safe-spend-card__review" data-testid="needs-review">
          <p class="safe-spend-card__secondary">
            Needs review (not reserved): {{ needsReview.length }}
            {{ needsReview.length === 1 ? 'bill' : 'bills' }}, {{ formatCents(needsReviewCents) }}
          </p>
          <ul v-show="reservedOpen" class="safe-spend-card__bills">
            <li v-for="bill in needsReview" :key="bill.id + bill.due_date" data-testid="review-row">
              <span class="safe-spend-card__bill-name">
                {{ bill.name }}
                <small>{{ bill.due_date }} · {{ reviewReason(bill) }}</small>
              </span>
              <span class="safe-spend-card__bill-amount">{{ formatCents(bill.amount_cents) }}</span>
            </li>
          </ul>
          <router-link
            class="safe-spend-card__review-link"
            :to="{ path: '/transactions', query: { tab: 'Recurring' } }"
            >Review recurring bills</router-link
          >
        </div>
      </section>

      <div class="safe-spend-card__footer">
        <span>{{ horizonLabel }}</span>
        <span v-if="payload.confidence" class="safe-spend-card__confidence">{{
          confidenceLabel
        }}</span>
      </div>
    </template>
    <div v-else class="safe-spend-card__empty">No spend guidance is available yet.</div>
  </section>
</template>

<script setup>
/**
 * Glanceable dashboard widget for day-of spending decisions.
 */
import { computed, ref } from 'vue'

const modeOptions = [
  { value: 'today', label: 'Today' },
  { value: 'until_payday', label: 'Until Payday' },
  { value: 'week', label: 'Next 7 Days' },
]

const props = defineProps({
  payload: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  selectedMode: { type: String, default: 'today' },
})

const emit = defineEmits(['update:mode'])

const primaryAmount = computed(() => props.payload?.amount_cents ?? 0)
const statusClass = computed(() => props.payload?.status || 'unknown')
const statusLabel = computed(() => String(props.payload?.status || 'unknown').replace(/_/g, ' '))
const protectedTotal = computed(() => props.payload?.total_protected_room_cents ?? null)
const warnings = computed(() => props.payload?.warnings || [])
const bufferNote = computed(() => {
  const buffer = props.payload?.components?.required_buffer_cents
  const standard = props.payload?.default_buffer_cents
  return buffer != null && buffer === standard ? ` (${formatCents(buffer)} default)` : ''
})
const horizonLabel = computed(() => {
  const end = props.payload?.protection_window?.end || props.payload?.horizon_end
  if (!end) return 'Horizon unavailable'
  return `Protected through ${end}`
})
const windowLines = computed(() => {
  const display = props.payload?.display_window
  const protection = props.payload?.protection_window
  if (!display || !protection) return []
  const lines = [`Showing ${display.start} to ${display.end}`]
  const basis = {
    day_before_payday: 'the day before payday',
    rolling_7_day: 'the rolling 7 days',
    fallback_14_day: '14-day fallback (payday not validated)',
  }[protection.basis]
  lines.push(`Protecting ${protection.start} to ${protection.end}${basis ? `: ${basis}` : ''}`)
  const payday = props.payload?.payday_prediction
  if (payday?.next_payday) {
    const kind = payday.needs_review ? 'inferred' : 'confirmed'
    lines.push(`Next payday ${payday.next_payday} (${kind}, ${payday.confidence} confidence)`)
  }
  return lines
})
const reservedOpen = ref(false)
const GROUPS = [
  { status: 'planned', label: 'Planned', component: 'planned_bills_cents' },
  { status: 'confirmed', label: 'Confirmed recurring', component: 'confirmed_recurring_cents' },
  {
    status: 'provisional',
    label: 'Provisional recurring',
    component: 'provisional_recurring_cents',
  },
]
// Groups use the server's component totals and rows; nothing is re-added on the client.
const reserveGroups = computed(() => {
  const bills = props.payload?.upcoming_bills || []
  return GROUPS.map((group) => ({
    ...group,
    total: props.payload?.components?.[group.component] ?? 0,
    rows: bills
      .filter((bill) => (bill.status || 'planned') === group.status)
      .slice()
      .sort((a, b) => String(a.due_date).localeCompare(String(b.due_date))),
  })).filter((group) => group.rows.length)
})
const needsReview = computed(() => props.payload?.needs_review_bills || [])
const needsReviewCents = computed(() => props.payload?.components?.needs_review_cents ?? 0)
const coverage = computed(() => props.payload?.obligation_coverage || {})
const reservedSummary = computed(() => {
  const reserved = props.payload?.components?.upcoming_outflows_cents ?? 0
  const dueNow = coverage.value.display_window_due_cents
  const end = props.payload?.protection_window?.end || props.payload?.horizon_end
  if (!reserved) return noReservedCopy.value
  if (dueNow == null) return `${formatCents(reserved)} reserved through ${end}.`
  const dueLabel = `${formatCents(dueNow)} due ${props.payload?.mode === 'today' ? 'today' : 'in this view'}`
  const later = Math.max(reserved - dueNow, 0)
  return later
    ? `${dueLabel}; ${formatCents(later)} more is protected for bills due before ${end}.`
    : `${dueLabel}; ${formatCents(reserved)} reserved through ${end}.`
})
const noReservedCopy = computed(() => {
  const end = props.payload?.protection_window?.end || props.payload?.horizon_end
  if (coverage.value.complete === false) {
    return `No bills are reserved through ${end}, but bill coverage is incomplete, so this may not be every bill.`
  }
  return `No known bills are reserved through ${end}.`
})
const beyondProtectionCopy = computed(() => {
  const end = props.payload?.protection_window?.end || props.payload?.horizon_end
  return end ? `Bills due after ${end} are not reserved yet.` : ''
})
const REVIEW_REASONS = {
  needs_review_insufficient_cycles: 'seen fewer than 3 times',
  needs_review_low_confidence: 'low confidence',
  stale_evidence: 'stale history',
}
function reviewReason(bill) {
  const code = (bill.reason_codes || []).find((c) => REVIEW_REASONS[c])
  return code ? REVIEW_REASONS[code] : 'needs review'
}
function accountName(accountId) {
  const match = (props.payload?.accounts || []).find((a) => a.account_id === accountId)
  return match?.name || ''
}
const confidenceLabel = computed(() => `Confidence: ${props.payload?.confidence || 'unknown'}`)

/**
 * Format integer cents as a compact USD amount.
 *
 * @param {number | null | undefined} cents Amount in cents.
 * @returns {string} Localized USD currency string.
 */
function formatCents(cents) {
  const dollars = Number(cents || 0) / 100
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: dollars % 1 === 0 ? 0 : 2,
  }).format(dollars)
}
</script>

<style scoped>
.safe-spend-card {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  gap: 1rem;
}

.safe-spend-card__header,
.safe-spend-card__amount-row,
.safe-spend-card__footer,
.safe-spend-card__components div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.safe-spend-card__kicker {
  margin: 0 0 0.25rem;
  color: var(--color-text-muted);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.safe-spend-card__title {
  margin: 0;
  color: var(--color-text-light);
  font-size: 1.15rem;
  font-weight: 800;
}

.safe-spend-card__status {
  border: 1px solid var(--divider);
  border-radius: 999px;
  color: var(--color-text-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 0.35rem 0.55rem;
  text-transform: uppercase;
}

.safe-spend-card__status--comfortable {
  border-color: var(--color-accent-green);
  color: var(--color-accent-green);
}

.safe-spend-card__status--caution,
.safe-spend-card__status--tight {
  border-color: var(--color-accent-yellow);
  color: var(--color-accent-yellow);
}

.safe-spend-card__status--do_not_spend {
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
}

.safe-spend-card__modes {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.safe-spend-card__mode {
  font-size: 0.72rem;
  padding: 0.35rem 0.55rem;
}

.safe-spend-card__amount {
  color: var(--color-accent-cyan);
  font-size: clamp(2rem, 5vw, 3.25rem);
  font-weight: 900;
  letter-spacing: -0.04em;
}

.safe-spend-card__amount-copy,
.safe-spend-card__footer,
.safe-spend-card__message,
.safe-spend-card__empty {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.safe-spend-card__message {
  line-height: 1.45;
  margin: 0;
}

.safe-spend-card__components {
  border-top: 1px solid var(--divider);
  display: grid;
  gap: 0.45rem;
  margin: 0;
  padding-top: 0.85rem;
}

.safe-spend-card__components dt,
.safe-spend-card__components dd {
  margin: 0;
}

.safe-spend-card__components dt {
  color: var(--color-text-muted);
}

.safe-spend-card__components dd {
  color: var(--color-text-light);
  font-weight: 800;
}

.safe-spend-card__secondary,
.safe-spend-card__windows,
.safe-spend-card__warnings {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  margin: 0;
}

.safe-spend-card__windows,
.safe-spend-card__warnings {
  list-style: none;
  padding: 0;
}

.safe-spend-card__warnings {
  color: var(--color-accent-yellow);
}

.safe-spend-card__reserved {
  border-top: 1px solid var(--divider);
  display: grid;
  gap: 0.5rem;
  padding-top: 0.85rem;
}

.safe-spend-card__reserved-toggle {
  align-items: center;
  background: none;
  border: 0;
  color: var(--color-text-light);
  cursor: pointer;
  display: flex;
  font-size: 0.85rem;
  font-weight: 800;
  justify-content: space-between;
  padding: 0.25rem 0;
  text-align: left;
  width: 100%;
}

.safe-spend-card__reserved-toggle:focus-visible,
.safe-spend-card__review-link:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.safe-spend-card__reserved-summary {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  margin: 0;
}

.safe-spend-card__group-title {
  color: var(--color-text-light);
  display: flex;
  font-size: 0.8rem;
  font-weight: 800;
  gap: 0.75rem;
  justify-content: space-between;
  margin: 0.35rem 0;
}

.safe-spend-card__bills {
  display: grid;
  gap: 0.35rem;
  list-style: none;
  margin: 0;
  padding: 0;
}

.safe-spend-card__bills li {
  align-items: flex-start;
  display: flex;
  font-size: 0.8rem;
  gap: 0.75rem;
  justify-content: space-between;
}

.safe-spend-card__bill-name {
  color: var(--color-text-light);
  min-width: 0;
  overflow-wrap: anywhere;
}

.safe-spend-card__bill-name small {
  color: var(--color-text-muted);
  display: block;
}

.safe-spend-card__bill-amount {
  flex-shrink: 0;
  font-weight: 800;
  white-space: nowrap;
}

.safe-spend-card__review-link {
  color: var(--color-accent-cyan);
  font-size: 0.8rem;
  font-weight: 700;
}

.safe-spend-card__confidence {
  text-transform: capitalize;
}

.safe-spend-card__empty {
  align-items: center;
  border: 1px dashed var(--divider);
  border-radius: var(--radius-md);
  display: flex;
  flex: 1;
  justify-content: center;
  min-height: 9rem;
  padding: 1rem;
  text-align: center;
}

.safe-spend-card__empty--error {
  border-color: var(--color-accent-red);
  color: var(--color-accent-red);
}
</style>
