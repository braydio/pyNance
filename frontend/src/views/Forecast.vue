<template>
  <div class="p-6 space-y-6 bg-gray-50 min-h-screen">
    <ForecastLayout />
  </div>
</template>

<script setup>
// Top-level Forecast page view, pulls together full mock forecast framework
import ForecastLayout from '@/components/forecast/ForecastLayout.vue'
</script>
<style scoped>
/* Layout polish for better spacing */
</style>
