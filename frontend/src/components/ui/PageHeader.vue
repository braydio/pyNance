<template>
  <Card class="p-6 flex items-center">
    <div class="flex-1" />
    <div class="text-center">
      <h1 class="text-2xl font-bold">
        <slot name="title" />
      </h1>
      <p v-if="$slots.subtitle" class="text-muted">
        <slot name="subtitle" />
      </p>
    </div>
    <div class="flex-1 flex items-center justify-end gap-2">
      <component v-if="icon" :is="icon" class="w-6 h-6" />
      <slot name="actions" />
    </div>
  </Card>
</template>

<script setup>
/**
 * PageHeader
 * Standard card header for views with an optional actions slot and trailing icon.
 *
 * Props:
 * - icon: optional icon component rendered on the right
 *
 * Slots:
 * - title: main heading text
 * - subtitle: supporting description text
 * - actions: optional right-aligned action controls
 */
import Card from '@/components/ui/Card.vue'

defineProps({
  icon: {
    type: [String, Object],
    default: null
  }
})
</script>
