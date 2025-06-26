<template>
  <div class="breakdown-panel">
    <h3 class="breakdown-header">Forecast Breakdown</h3>
    <ul class="breakdown-list">
      <li v-for="(item, i) in forecastItems" :key="i">
        <span class="label">{{ item.label }}</span>
        <span class="amount">{{ item.amount < 0 ? '-' : '+' }}${{ Math.abs(item.amount) }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  forecastItems: Array,
  viewType: String
})
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
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.label {
  color: var(--text-muted);
}

.amount {
  font-weight: bold;
}
</style>
