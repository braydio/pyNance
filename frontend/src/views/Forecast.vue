<!-- Forecast.vue - Entry point for forecasting dashboard. -->
<template>
  <BasePageLayout class="forecast-view">
    <ForecastLayout />
  </BasePageLayout>
</template>

<script setup>
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
.forecast-view {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
}
</style>
