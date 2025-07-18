<template>
  <table class="min-w-full divide-y divide-[var(--divider)]">
    <thead class="bg-[var(--color-bg)] text-[var(--theme-fg)] text-sm font-semibold">
      <tr>
        <th class="px-3 py-2">Recurring ID</th>
        <th class="px-3 py-2">Status</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(action, idx) in results" :key="idx" class="even:bg-[var(--color-bg-secondary)]">
        <td class="px-3 py-2">{{ action.recurring_id }}</td>
        <td class="px-3 py-2">{{ action.status }}</td>
      </tr>
      <tr v-if="!results.length">
        <td colspan="2" class="px-3 py-2 text-[var(--color-text-muted)] text-center">No actions detected.</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
const { results } = defineProps({
  results: { type: Array, default: () => [] }
});
</script>
