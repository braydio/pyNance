<template>
  <div class="breakdown">
    <h2>Forecast Breakdown ({{ viewType }})</h2>
    <ul>
      <li v-for="(item, index) in forecastItems" :key="index">
        {{ item.label }}: ${{ item.amount }}
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
  padding: 1rem;
  border: 1px solid #ccc;
}
</style>
