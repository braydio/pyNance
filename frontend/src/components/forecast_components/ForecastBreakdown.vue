<template>
  <div class="bg-white rounded-2xl shadow p-6 space-y-2">
    <h2 class="text-xl font-semibold">Forecast Breakdown</h2>
    <ul class="space-y-1 text-sm">
      <li v-for="item in forecastItems" :key="item.label">
        <span :class="item.amount >= 0 ? 'text-green-600' : 'text-red-500'">
          {{ item.amount >= 0 ? '+' : '' }}${{ item.amount }}
        </span>
        – {{ item.label }}
      </li>
    </ul>
  </div>
</template>

<script setup>
defineProps(['forecastItems'])
</script>
