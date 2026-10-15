<template>
  <section
    class="scenario-comparison card glass"
    data-testid="scenario-comparison"
    aria-labelledby="scenario-comparison-title"
  >
    <h3 id="scenario-comparison-title" class="scenario-title">What if…?</h3>
    <fieldset class="scenario-options">
      <legend class="scenario-legend">Compare against your baseline forecast</legend>
      <label v-for="preset in presets" :key="preset.id" class="scenario-option">
        <input
          type="checkbox"
          :value="preset.id"
          :checked="selectedIds.includes(preset.id)"
          :disabled="!selectedIds.includes(preset.id) && selectedIds.length >= maxSelected"
          @change="toggle(preset.id)"
        />
        {{ preset.label }}
      </label>
    </fieldset>

    <p v-if="loading" class="scenario-muted" role="status">Updating scenarios…</p>
    <p v-else-if="rows.length === 0" class="scenario-muted" data-testid="scenario-empty">
      Pick a scenario to see how your ending and lowest cash change. Scenarios are replayed through
      the same forecast engine and are not saved.
    </p>
    <div
      v-else
      class="scenario-table-wrap"
      role="region"
      aria-label="Scenario comparison table"
      tabindex="0"
    >
      <table class="scenario-table">
        <thead>
          <tr>
            <th scope="col">Scenario</th>
            <th scope="col">Cash at end</th>
            <th scope="col">Change vs baseline</th>
            <th scope="col">Lowest cash</th>
            <th scope="col">First shortfall</th>
            <th v-if="hasRisk" scope="col">Chance below $0</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id" :data-testid="`scenario-row-${row.id}`">
            <th scope="row">{{ row.label }}</th>
            <td>{{ money(row.ending_cash) }}</td>
            <td :class="deltaClass(row.delta_vs_baseline.ending_cash)">
              {{ row.id === 'baseline' ? '—' : signed(row.delta_vs_baseline.ending_cash) }}
            </td>
            <td>{{ money(row.min_cash) }}</td>
            <td>{{ row.first_shortfall_date || 'None projected' }}</td>
            <td v-if="hasRisk">
              {{ row.risk ? percent(row.risk.probability_cash_below_zero_any_day) : '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ForecastScenarioResult } from '@/composables/useForecastData'

export type ScenarioPreset = { id: string; label: string }

const props = withDefaults(
  defineProps<{
    presets: ScenarioPreset[]
    selectedIds: string[]
    results?: ForecastScenarioResult[]
    loading?: boolean
    maxSelected?: number
  }>(),
  { results: () => [], loading: false, maxSelected: 5 },
)

const emit = defineEmits<{ (_event: 'update:selectedIds', _ids: string[]): void }>()

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const money = (value: number) => currency.format(value)
const signed = (value: number) => `${value < 0 ? '-' : '+'}${currency.format(Math.abs(value))}`
const percent = (value: number) => `${Math.round(value * 100)}%`
const deltaClass = (value: number) => ({
  'scenario-up': value > 0,
  'scenario-down': value < 0,
})

const rows = computed(() => (props.results.length > 1 ? props.results : []))
const hasRisk = computed(() => rows.value.some((row) => row.risk))

function toggle(id: string) {
  const next = props.selectedIds.includes(id)
    ? props.selectedIds.filter((item) => item !== id)
    : [...props.selectedIds, id]
  emit('update:selectedIds', next)
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.scenario-comparison {
  display: grid;
  gap: 0.75rem;
}

.scenario-title {
  font-size: 1.125rem;
  font-weight: 600;
}

.scenario-options {
  border: 0;
  padding: 0;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
}

.scenario-legend {
  font-size: 0.8125rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.scenario-option {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.9rem;
}

.scenario-option input:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.scenario-muted {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin: 0;
}

.scenario-table-wrap {
  overflow-x: auto;
  max-width: 100%;
}

.scenario-table-wrap:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.scenario-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
  white-space: nowrap;
}

.scenario-table th,
.scenario-table td {
  padding: 0.35rem 0.6rem;
  text-align: right;
  border-bottom: 1px solid var(--divider);
}

.scenario-table th:first-child {
  text-align: left;
}

.scenario-up {
  color: var(--text-positive);
}

.scenario-down {
  color: var(--text-negative);
}
</style>
