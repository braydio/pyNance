<template>
  <Card class="p-6 flex items-center justify-center gap-3 text-center">
    <component :is="icon" v-if="icon" class="w-6 h-6" />
    <div>
      <h1 class="text-2xl font-bold">{{ title }}</h1>
      <p v-if="subtitle" class="text-muted">{{ subtitle }}</p>
    </div>
  </Card>
</template>

<script setup>
import Card from '@/components/ui/Card.vue'
/**
 * PageHeader displays a centered heading block with optional icon,
 * title, and subtitle. It is intended to provide a consistent page
 * header across views.
 */
defineProps({
  // Header title text
  title: { type: String, required: true },
  // Optional subtitle displayed under the title
  subtitle: { type: String, default: '' },
  // Optional icon component from lucide-vue-next
  icon: { type: Object, default: null },
})
</script>
