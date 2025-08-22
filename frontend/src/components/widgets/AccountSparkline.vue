<!--
  AccountSparkline.vue
  Renders a simple SVG sparkline for an account's balance or transaction history.
  Supports toggle between balance history and transaction activity.
-->
<template>
  <div class="sparkline-container" @click="toggleDataType" :title="toggleTitle">
    <svg v-if="points" viewBox="0 0 100 100" class="bs-sparkline" role="img" :aria-label="ariaLabel">
      <polyline :points="points" :class="sparklineClass" />
    </svg>
    <span v-else class="bs-sparkline-placeholder" role="img" :aria-label="noDataLabel"></span>
    <div class="sparkline-indicator" :class="indicatorClass">{{ dataTypeIndicator }}</div>
  </div>
</template>

<script setup>
import { ref, computed, toRef } from 'vue'
import { useAccountHistory } from '@/composables/useAccountHistory'
import { useAccountTransactionHistory } from '@/composables/useAccountTransactionHistory'

const props = defineProps({
  accountId: { type: String, required: true }
})

// Data type: 'balance' or 'transactions'
const dataType = ref('balance')

// Fetch both types of data
const { history: balanceHistory } = useAccountHistory(toRef(props, 'accountId'))

// Only fetch transaction history if the composable is available
// For now, fall back to balance data to ensure functionality
let transactionHistory
try {
  const { history } = useAccountTransactionHistory(toRef(props, 'accountId'))
  transactionHistory = history
} catch {
  // Fallback to balance history if transaction history composable fails
  console.warn('Transaction history not available, using balance history as fallback')
  transactionHistory = balanceHistory
}

// Toggle between data types
function toggleDataType() {
  dataType.value = dataType.value === 'balance' ? 'transactions' : 'balance'
}

// Computed properties for UI
const toggleTitle = computed(() => 
  `Click to toggle to ${dataType.value === 'balance' ? 'transaction' : 'balance'} view`
)

const dataTypeIndicator = computed(() => 
  dataType.value === 'balance' ? 'B' : 'T'
)

const indicatorClass = computed(() => ({
  'indicator-balance': dataType.value === 'balance',
  'indicator-transactions': dataType.value === 'transactions'
}))

const sparklineClass = computed(() => ({
  'sparkline-balance': dataType.value === 'balance',
  'sparkline-transactions': dataType.value === 'transactions'
}))

const ariaLabel = computed(() => 
  `Recent ${dataType.value} history for account ${props.accountId}`
)

const noDataLabel = computed(() => 
  `No ${dataType.value} history available`
)

// Current data based on selected type
const currentData = computed(() => 
  dataType.value === 'balance' ? balanceHistory.value : transactionHistory.value
)

// Generate sparkline points
const points = computed(() => {
  const data = currentData.value
  if (!data.length) return ''
  
  let values
  if (dataType.value === 'balance') {
    values = data.map(d => d.balance)
  } else {
    // For transactions, use net amounts or transaction counts
    values = data.map(d => d.net_amount || d.transaction_count || 0)
  }
  
  const max = Math.max(...values)
  const min = Math.min(...values)
  const range = max - min || 1
  
  return data
    .map((d, idx) => {
      const x = (idx / (data.length - 1)) * 100
      const y = 100 - ((values[idx] - min) / range) * 100
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<style scoped>
.sparkline-container {
  position: relative;
  width: 60px;
  height: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sparkline-container:hover {
  transform: scale(1.05);
}

.bs-sparkline {
  width: 100%;
  height: 100%;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.5;
  transition: stroke 0.3s ease;
}

.sparkline-balance {
  stroke: var(--color-accent-cyan);
}

.sparkline-transactions {
  stroke: var(--color-accent-yellow);
}

.bs-sparkline-placeholder {
  width: 100%;
  height: 100%;
  background: var(--color-bg-dark);
  border-radius: 2px;
  opacity: 0.3;
}

.sparkline-indicator {
  position: absolute;
  bottom: -1px;
  right: -1px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  font-size: 6px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-bg-dark);
  transition: all 0.3s ease;
}

.indicator-balance {
  background: var(--color-accent-cyan);
}

.indicator-transactions {
  background: var(--color-accent-yellow);
}

.sparkline-container:hover .sparkline-indicator {
  transform: scale(1.2);
  box-shadow: 0 0 8px currentColor;
}
</style>
