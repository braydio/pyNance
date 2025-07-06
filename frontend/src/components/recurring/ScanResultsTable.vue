<template>
  <table class="min-w-full divide-y divide-gray-200">
    <thead class="bg-gray-100 text-gray-700 text-sm font-semibold">
      <tr>
        <th class="px-3 py-2">Recurring ID</th>
        <th class="px-3 py-2">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(action, idx) in results" :key="idx" class="even:bg-gray-50">
        <td class="px-3 py-2">{{ action.recurring_id }}</td>
        <td class="px-3 py-2">{{ action.status }}</td>
      </tr>
      <tr v-if="!results.length">
        <td colspan="2" class="px-3 py-2 text-gray-500 text-center">No actions detected.</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
const { results } = defineProps({
  results: { type: Array, default: () => [] }
});
</script>
