<template>
  <ul class="list-disc list-inside space-y-1">
    <li v-for="(action, idx) in results" :key="idx">
      <span class="font-semibold">ID:</span> {{ action.recurring_id }} -
      <span class="italic">{{ action.status }}</span>
    </li>
    <li v-if="!results.length" class="text-gray-500">No actions detected.</li>
  </ul>
</template>

<script setup>
const props = defineProps({
  results: { type: Array, default: () => [] }
});
</script>
