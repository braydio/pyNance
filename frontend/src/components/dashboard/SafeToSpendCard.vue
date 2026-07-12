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
        <span class="safe-spend-card__amount-copy">{{ amountCopy }}</span>
      </div>
      <p class="safe-spend-card__message">{{ payload.message }}</p>

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
          <dt>Protected buffer</dt>
          <dd>-{{ formatCents(payload.components?.required_buffer_cents) }}</dd>
        </div>
        <div>
          <dt>Spent today</dt>
          <dd>-{{ formatCents(payload.components?.spent_today_cents) }}</dd>
        </div>
      </dl>

      <div class="safe-spend-card__footer">
        <span>{{ horizonLabel }}</span>
        <span class="safe-spend-card__confidence">{{ confidenceLabel }}</span>
      </div>
    </template>
    <div v-else class="safe-spend-card__empty">No spend guidance is available yet.</div>
  </section>
</template>

<script setup>
/**
 * Glanceable dashboard widget for day-of spending decisions.
 */
import { computed } from 'vue'

const modeOptions = [
  { value: 'today', label: 'Today' },
  { value: 'until_payday', label: 'Until Payday' },
  { value: 'week', label: 'This Week' },
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
const amountCopy = computed(() => (props.selectedMode === 'today' ? 'available today' : 'per day'))
const horizonLabel = computed(() => {
  if (!props.payload?.horizon_end) return 'Horizon unavailable'
  if (props.selectedMode === 'today') return `As of ${props.payload.as_of}`
  return `Through ${props.payload.horizon_end}`
})
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
