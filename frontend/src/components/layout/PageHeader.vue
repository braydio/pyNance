<template>
  <Card class="p-6 flex flex-col items-center text-center gap-2">
    <component v-if="icon" :is="icon" class="w-8 h-8" />
    <div>
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <p v-if="subtitle" class="text-muted">{{ subtitle }}</p>
    </div>
  </Card>
</template>

<script setup>
/**
 * PageHeader provides a consistent card-style header with optional icon and subtitle.
 */
import Card from '@/components/ui/Card.vue'

defineProps({
  /** Main heading text for the page */
  title: { type: String, required: true },
  /** Optional subtitle displayed below the title */
  subtitle: { type: String, default: '' },
  /** Optional icon component rendered above the title */
  icon: { type: [Object, Function], default: null },
})
</script>
