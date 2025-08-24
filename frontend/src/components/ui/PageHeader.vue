<template>
  <Card class="p-6 flex items-center">
    <div class="flex items-center gap-3 flex-1">
      <slot name="icon" />
      <div>
        <h1 class="text-2xl font-bold">
          <slot name="title" />
        </h1>
        <p class="text-muted">
          <slot name="subtitle" />
        </p>
      </div>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2 ml-auto">
      <slot name="actions" />
    </div>
  </Card>
</template>

<script setup>
/**
 * PageHeader
 * Standard card header for views with an optional actions slot.
 *
 * Slots:
 * - icon: optional leading icon
 * - title: main heading text
 * - subtitle: supporting description text
 * - actions: optional right-aligned action controls
 */
import Card from '@/components/ui/Card.vue'
</script>
