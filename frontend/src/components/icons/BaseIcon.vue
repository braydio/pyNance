<template>
  <svg v-if="name === 'x'" xmlns="http://www.w3.org/2000/svg" :class="iconClass" fill="none" viewBox="0 0 24 24"
    stroke="currentColor" stroke-width="2">
    <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
  </svg>
  <svg v-else-if="name === 'plus-circle'" xmlns="http://www.w3.org/2000/svg" :class="iconClass" fill="none"
    viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10" stroke-opacity="0.7" />
    <path d="M7 12h10M12 7v10" stroke-linecap="round" />
  </svg>
  <!-- Add other icons as needed -->
</template>

<script setup>
defineProps({
  name: { type: String, required: true },
  iconClass: { type: String, default: '' }
})
</script>
