<template>
  <div class="bg-white rounded-2xl shadow p-6 space-y-4">
    <h2 class="text-xl font-semibold">Forecast Breakdown - {{ viewType }} View</h2>

    <div v-for="section in breakdownData" :key="section.label" class="space-y-1">
      <h3 class="text-sm font-medium text-gray-600">{{ section.label }}</h3>
      <ul class="text-sm space-y-1 pl-4">
        <li v-for="item in section.items" :key="item.label" class="flex justify-between">
          <span>{{ item.label }}</span>
          <span :class="item.amount >= 0 ? 'text-green-600' : 'text-red-500'">
            {{ item.amount >= 0 ? '+' : '' }}${{ item.amount.toFixed(2) }}
          </span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  forecastItems: Array,
  viewType: String
})

const breakdownData = [
  {
    label: 'Forecast',
    items: props.forecastItems.map(item => ({
      label: item.label,
      amount: item.amount * (props.viewType === 'Year' ? 12 : 1)
    }))
  },
  {
    label: 'Manual Adjustments',
    items: [
      { label: 'Bonus Estimate', amount: 800 },
      { label: 'Holiday Spending', amount: -300 }
    ]
  },
  {
    label: 'Actuals',
    items: props.forecastItems.map(item => ({
      label: item.label,
      amount: (item.amount + Math.random() * 100 - 50)
    }))
  }
]
</script>

<style scoped>
ul {
  list-style-type: disc;
}
</style>
