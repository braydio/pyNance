<!--
  Forecast.vue
  Page displaying forecast charts and summaries.
-->
<template>
  <BasePageLayout>
    <template #header>
      <PageHeader title="Forecasting" :icon="TrendingUp" />
    </template>
    <ForecastLayout />
  </BasePageLayout>
</template>

<script setup>
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { TrendingUp } from 'lucide-vue-next'
</script>

