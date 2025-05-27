<template>
  <div class="relative h-64 w-full">
    <canvas ref="chartRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
  type: { type: String, required: true },
  data: { type: Object, required: true },
  options: { type: Object, default: () => ({}) },
});

const chartRef = ref(null);
let chartInstance = null;

onMounted(() => {
  if (chartRef.value) {
    chartInstance = new Chart(chartRef.value.getContext('2d'), {
      type: props.type,
      data: props.data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#4B5563' } },
          tooltip: {
            backgroundColor: '#1F2937',
            titleColor: '#ffffff',
            bodyColor: '#ffffff',
          },
        },
        scales: {
          x: { ticks: { color: '#4B5563' }, grid: { color: '#E5E7EB' } },
          y: { ticks: { color: '#4B5563' }, grid: { color: '#E5E7EB' } },
        },
        ...props.options,
      },
    });
  }
});

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.destroy();
  }
});
</script>