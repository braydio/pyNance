<template>
  <div class="flex items-center justify-between text-gray-600 text-sm mt-4">
    <button
      class="btn"
      :class="{ 'opacity-50 cursor-not-allowed': currentPage <= 1 }"
      @click="$emit('change', -1)"
      :disabled="currentPage <= 1"
    >
      Previous
    </button>
    <span>Page {{ currentPage }} of {{ totalPages }}</span>
    <button
      class="btn"
      :class="{ 'opacity-50 cursor-not-allowed': currentPage >= totalPages }"
      @click="$emit('change', 1)"
      :disabled="currentPage >= totalPages"
    >
      Next
    </button>
  </div>
</template>

<script setup>
defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
});
</script>