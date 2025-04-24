<template>
  <button :class="computedClass" :disabled="disabled" @click="$emit('click', $event)">
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  variant: {
    type: String,
    default: '', // 'outline', 'success', 'alert'
  },
  pill: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const computedClass = computed(() => {
  return [
    'btn',
    props.variant && `btn-${props.variant}`,
    props.pill && 'btn-pill',
  ]
    .filter(Boolean)
    .join(' ');
});
</script>
