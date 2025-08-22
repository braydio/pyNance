<template>
  <div class="planning-view">
    <h1 class="text-2xl font-bold mb-4">Planning</h1>
    <pre>{{ JSON.stringify(state, null, 2) }}</pre>
  </div>
</template>

<script setup>
import { usePlanning } from '@/composables/usePlanning'

/**
 * Top-level view for budgeting and allocation planning.
 * Currently displays the raw planning state as a scaffold.
 */
const { state } = usePlanning()
</script>

<style scoped>
@reference "../assets/css/main.css";
.planning-view {
  background-color: var(--page-bg);
  color: var(--theme-fg);
  min-height: 100vh;
  padding: 1.5rem;
}
</style>
