<template>
  <div class="summary-panel">
    <h2>Summary</h2>
    <p>Current Balance: ${{ currentBalance }}</p>
    <p>Manual Income: ${{ manualIncome }}</p>
    <p>Liability Rate: {{ (liabilityRate * 100).toFixed(2) }}%</p>
    <p>View Type: {{ viewType }}</p>
  </div>
</template>

<script setup>
defineProps({
  currentBalance: Number,
  manualIncome: Number,
  liabilityRate: Number,
  viewType: String,
})
</script>

<style scoped>
.summary-panel {
  padding: 1rem;
  border: 1px solid #ccc;
}
</style>
