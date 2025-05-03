<template>
  <div class="breakdown bg-white p-4 rounded shadow space-y-2">
    <h2 class="text-lg font-semibold">Forecast Breakdown ({{ viewType }})</h2>
    <ul class="space-y-1">
      <li v-for="(item, index) in forecastItems" :key="index" class="text-sm">
        {{ item.label }}: ${{ item.amount.toFixed(2) }}
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  forecastItems: Array,
  viewType: String,
})
</script>

<style scoped>
.breakdown {
  border: 1px solid #ccc;
}
</style>
