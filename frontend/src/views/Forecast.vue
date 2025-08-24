<template>
  <BasePageLayout>
    <template #header>
      <PageHeader title="Forecasting" :icon="LineChart" />
    </template>
    <ForecastLayout />
  </BasePageLayout>
</template>

<script setup>
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import { LineChart } from 'lucide-vue-next'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
