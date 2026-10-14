<template>
  <button :class="computedClass" :disabled="disabled" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

// Declared so a parent's @click is delivered by this emit only. Undeclared, it also
// fell through to the root <button> and every click handler ran twice.
defineEmits(['click'])

const props = defineProps({
  variant: {
    type: String,
    default: '', // 'outline', 'primary', 'success', 'alert'
  },
  pill: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const computedClass = computed(() => {
  return ['btn', props.variant && `btn-${props.variant}`, props.pill && 'btn-pill']
    .filter(Boolean)
    .join(' ')
})
</script>
