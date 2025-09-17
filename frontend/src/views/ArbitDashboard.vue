<template>
  <BasePageLayout class="arbit-dashboard" gap="gap-10">
    <PageHeader :icon="Activity">
      <template #title>Arbitrage Command Center</template>
      <template #subtitle>Monitor engine status, opportunities, and trades</template>
    </PageHeader>

    <section data-testid="status-controls" class="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <Card class="h-full p-6 space-y-4">
        <h2 class="section-title">Engine Status</h2>
        <ArbitStatus />
      </Card>
      <Card class="h-full p-6 space-y-4 xl:col-span-2">
        <h2 class="section-title">Control Panel</h2>
        <ArbitControls />
      </Card>
    </section>

    <section data-testid="metrics-alerts" class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <Card class="h-full p-6 space-y-4 lg:col-span-2">
        <h2 class="section-title">Performance Metrics</h2>
        <ArbitMetrics />
      </Card>
      <Card class="h-full p-6 space-y-4">
        <h2 class="section-title">Live Alerts</h2>
        <ArbitAlerts />
      </Card>
    </section>

    <section data-testid="opportunities-trades" class="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <Card class="h-full p-6 space-y-4">
        <h2 class="section-title">Current Opportunities</h2>
        <ArbitOpportunities />
      </Card>
      <Card class="h-full p-6 space-y-4 xl:col-span-2 overflow-x-auto">
        <h2 class="section-title">Recent Trades</h2>
        <ArbitTrades />
      </Card>
    </section>
  </BasePageLayout>
</template>

<script setup>
/**
 * High-level arbitrage dashboard combining status, controls, metrics, alerts,
 * opportunities, and trades into a single operational view.
 */
import { Activity } from 'lucide-vue-next'
import ArbitAlerts from '@/components/ArbitAlerts.vue'
import ArbitControls from '@/components/ArbitControls.vue'
import ArbitMetrics from '@/components/ArbitMetrics.vue'
import ArbitOpportunities from '@/components/ArbitOpportunities.vue'
import ArbitStatus from '@/components/ArbitStatus.vue'
import ArbitTrades from '@/components/ArbitTrades.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";

.arbit-dashboard {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--color-accent-cyan);
}
</style>
