<template>
  <div class="p-6 space-y-4">
    <h1 class="text-2xl font-bold text-[var(--color-accent-yellow)]">
      R/S Arbitrage Monitor
    </h1>
    <pre
      v-if="content"
      class="bg-gray-800 text-white p-4 rounded whitespace-pre-wrap"
    >{{ content }}</pre>
    <div v-else>Loading...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchArbitrageData } from '@/api/arbitrage'

const content = ref('')

const load = async () => {
  try {
    const data = await fetchArbitrageData()
    content.value = data.content || JSON.stringify(data, null, 2)
  } catch (err) {
    console.error('Failed to load arbitrage data', err)
  }
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>
