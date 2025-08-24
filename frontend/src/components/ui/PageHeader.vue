<template>
  <header class="flex flex-col items-center text-center gap-2">
    <component v-if="icon" :is="icon" class="w-8 h-8" />
    <div>
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <p v-if="subtitle" class="text-muted">{{ subtitle }}</p>
    </div>
  </header>
</template>

<script setup>
/**
 * PageHeader renders a centered title with optional subtitle and icon.
 * It standardizes headers across pages for visual consistency.
 */
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  icon: { type: [Object, Function], default: null },
})
</script>

<style scoped>
@reference "../../assets/css/main.css";
</style>

