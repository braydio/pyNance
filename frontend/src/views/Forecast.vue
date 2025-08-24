<!-- Forecast.vue - Entry point for forecasting dashboard. -->
<template>
  <BasePageLayout class="forecast-view">
    <PageHeader :icon="LineChart">
      <template #title>Forecast</template>
      <template #subtitle>Project your financial future</template>
    </PageHeader>
    <ForecastLayout />
  </BasePageLayout>
</template>

<script setup>
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { LineChart } from 'lucide-vue-next'
</script>

<style scoped>
@reference "../assets/css/main.css";
.forecast-view {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
}
</style>
