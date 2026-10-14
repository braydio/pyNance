<template>
  <div class="breakdown-panel">
    <h3 class="breakdown-header">Forecast Breakdown</h3>
    <ul v-if="forecastItems.length" class="breakdown-list">
      <li v-for="(item, i) in forecastItems" :key="i">
        <button type="button" class="line-item-button" @click="emit('select-item', item)">
          <span class="label">{{ item.label }}</span>
          <span class="amount">{{ item.amount < 0 ? '-' : '+' }}${{ Math.abs(item.amount) }}</span>
        </button>
      </li>
    </ul>
    <p v-else class="breakdown-empty">No forecast cashflows available.</p>

    <details v-if="modelVersion === 'v2'" class="drivers-details" data-testid="forecast-drivers">
      <summary class="drivers-summary">
        What drives this forecast: {{ drivers.length }} scheduled events plus typical spending
      </summary>
      <p class="drivers-note">
        Bills and paychecks below are placed on their expected dates. Everyday spending is estimated
        separately from your recent history, so these events are not counted twice.
      </p>
      <ul v-if="drivers.length" class="drivers-list">
        <li v-for="driver in drivers" :key="driver.event_id" class="driver-row">
          <span class="driver-date">{{ driver.date }}</span>
          <span class="driver-label">{{ driver.label || driver.kind.replace('_', ' ') }}</span>
          <span class="driver-origin" :data-confidence="driver.confidence_label">
            {{ originLabel(driver.origin) }} · {{ driver.confidence_label }} confidence
          </span>
          <strong class="driver-amount">{{ signed(driver.amount) }}</strong>
        </li>
      </ul>
      <p v-else class="breakdown-empty">No scheduled bills or paychecks were detected.</p>

      <div v-if="dataQuality" class="data-quality" data-testid="data-quality">
        <p>
          Based on {{ dataQuality.history_days }} days of history up to {{ dataQuality.as_of_date }}
          <span v-if="dataQuality.confidence"> ({{ dataQuality.confidence }} coverage)</span>.
          <span v-if="dataQuality.proposed_streams">
            {{ dataQuality.proposed_streams }} possible recurring item(s) need more history before
            they are used.
          </span>
        </p>
        <ul v-if="dataQuality.warnings.length" class="data-quality-warnings">
          <li v-for="(warning, index) in dataQuality.warnings" :key="`${warning.code}-${index}`">
            {{ warning.message }}
          </li>
        </ul>
      </div>
    </details>
  </div>
</template>

<script setup lang="ts">
import type {
  ForecastCashflowItem,
  ForecastDataQuality,
  ForecastDriver,
} from '@/composables/useForecastData'

withDefaults(
  defineProps<{
    forecastItems: ForecastCashflowItem[]
    viewType: string
    modelVersion?: string
    drivers?: ForecastDriver[]
    dataQuality?: ForecastDataQuality | null
  }>(),
  { modelVersion: 'v1', drivers: () => [], dataQuality: null },
)

const ORIGIN_LABELS: Record<string, string> = {
  manual_rule: 'Your rule',
  confirmed_recurring: 'Confirmed recurring',
  detected_recurring: 'Detected pattern',
}
const originLabel = (origin: string) => ORIGIN_LABELS[origin] ?? origin
const signed = (value: number) =>
  `${value < 0 ? '-' : '+'}$${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

const emit = defineEmits<{
  (_event: 'select-item', _item: ForecastCashflowItem): void
}>()
</script>

<style scoped>
@reference "../../assets/css/main.css";
.breakdown-panel {
  background: var(--surface);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
}

.breakdown-header {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.drivers-details {
  margin-top: 1rem;
  border-top: 1px solid var(--divider);
  padding-top: 0.75rem;
}

.drivers-summary {
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
}

.drivers-note,
.data-quality {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0.5rem 0;
}

.drivers-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.25rem;
}

.driver-row {
  display: grid;
  grid-template-columns: 6rem 1fr auto;
  gap: 0.5rem;
  align-items: baseline;
  font-size: 0.85rem;
}

.driver-origin {
  grid-column: 2 / 3;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.driver-amount {
  grid-row: 1 / 3;
  grid-column: 3;
}

.breakdown-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.breakdown-list li {
  margin-bottom: 0.5rem;
}

.line-item-button {
  width: 100%;
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  text-align: left;
  padding: 0.4rem 0.5rem;
  border-radius: 0.4rem;
  border: 1px solid transparent;
  background: transparent;
}

.line-item-button:hover {
  border-color: rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.08);
}

.label {
  color: var(--text-muted);
}

.amount {
  font-weight: bold;
}

.breakdown-empty {
  font-size: 0.9rem;
  color: var(--text-muted);
}
</style>
