<template>
  <div class="forecast-view">
    <ForecastLayout />
  </div>
</template>

<script setup>
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
.forecast-view {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
