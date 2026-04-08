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
  </div>
</template>

<script setup lang="ts">
import type { ForecastCashflowItem } from '@/composables/useForecastData'

defineProps<{
  forecastItems: ForecastCashflowItem[]
  viewType: string
}>()

const emit = defineEmits<{
  (event: 'select-item', item: ForecastCashflowItem): void
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
