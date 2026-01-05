<!--
  InsightsRow.vue
  Layout wrapper pairing a primary dashboard card with spending insights.
-->
<template>
  <div class="grid grid-cols-1 gap-6 md:grid-cols-3 items-stretch">
    <div class="md:col-span-2">
      <slot />
    </div>
    <SpendingInsights />
  </div>
</template>

<script setup>
/**
 * Positions a main dashboard widget alongside the insights module.
 */
import SpendingInsights from '@/components/SpendingInsights.vue'
</script>
