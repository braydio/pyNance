<template>
  <div class="text-center py-4 space-y-2" data-testid="retry-error">
    <p class="text-error">{{ message }}</p>
    <UiButton variant="outline" @click="$emit('retry')" data-testid="retry-button">Retry</UiButton>
  </div>
</template>

<script setup>
import UiButton from '@/components/ui/Button.vue'

// RetryError.vue - Shows an error message with a retry option.

defineProps({
  message: { type: String, default: 'Something went wrong' }
})

defineEmits(['retry'])
</script>
