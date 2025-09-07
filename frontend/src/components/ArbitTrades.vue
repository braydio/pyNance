<template>
  <table data-testid="trades-table">
    <thead>
      <tr>
        <th>Pair</th>
        <th>Profit</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="t in trades" :key="t.id">
        <td>{{ t.pair }}</td>
        <td>{{ t.profit }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
/**
 * Displays recent arbitrage trades.
 */
import { ref, onMounted } from 'vue'
import { fetchArbitTrades } from '@/services/arbit'

const trades = ref([])

async function load() {
  const data = await fetchArbitTrades()
  trades.value = data.trades || []
}

onMounted(load)
</script>
