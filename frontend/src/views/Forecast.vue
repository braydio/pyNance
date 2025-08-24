<template>
  <AppLayout>
    <template #header>
      <PageHeader title="Forecasting" subtitle="Project your balances" :icon="LineChart" />
    </template>
    <ForecastLayout />
  </AppLayout>
</template>

<script setup>
import AppLayout from '@/components/layout/AppLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
import { LineChart } from 'lucide-vue-next'
</script>
