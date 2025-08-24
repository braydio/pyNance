<template>
  <BasePageLayout>
    <template #header>
      <PageHeader title="Investments" />
    </template>

    <section class="mb-6">
      <h2 class="text-xl font-semibold mb-2">Portfolio Overview</h2>
      <p class="text-muted">Key portfolio metrics will appear here.</p>
    </section>

    <section class="mb-6">
      <h2 class="text-xl font-semibold mb-2">Holdings</h2>
      <p class="text-muted">Table of holdings placeholder.</p>
    </section>

    <section>
      <h2 class="text-xl font-semibold mb-2">Performance</h2>
      <p class="text-muted">Charts and performance indicators placeholder.</p>
    </section>
  </BasePageLayout>
</template>

<script setup>
/**
 * Skeleton layout for the future Investments dashboard.
 * Replace placeholders with real data and components.
 */
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
