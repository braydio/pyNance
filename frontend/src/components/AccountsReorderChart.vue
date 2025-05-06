<template>
  <div class="chart-container card">
    <h2 class="heading-md">Top Credit Accounts</h2>
    <div class="bar-chart">
      <div v-for="account in topAccounts" :key="account.id" class="bar-row">
        <span class="bar-label">{{ account.name }}</span>
        <div class="bar-outer">
          <div class="bar-fill" :style="{ width: barWidth(account) }">
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import axios from 'axios'
import { ref, computed, onMounted } from 'vue'

const accounts = ref([])

function format(n) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

function barWidth(acc) {
  const max = Math.max(...accounts.value.map(a => Math.abs(a.adjusted_balance || a.balance)), 1)
  return `${(Math.abs(acc.adjusted_balance || acc.balance) / max) * 100}%`
}

const topAccounts = computed(() =>
  accounts.value
    .filter(a => a.type?.toLowerCase() === 'credit')
    .sort((a, b) => b.adjusted_balance - a.adjusted_balance)
    .slice(0, 5)
)

async function fetchAccounts() {
  const { data } = await axios.get('/api/accounts/get_accounts')
  if (data.status === 'success') {
    accounts.value = data.accounts.map(acc => ({
      ...acc,
      adjusted_balance: -Math.abs(acc.balance)
    }))
  }
}

onMounted(fetchAccounts)
</script>

<style scoped>
.chart-container {
  padding: 1rem;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bar-label {
  flex: 1;
  color: var(--color-text-muted);
}

.bar-outer {
  flex: 5;
  background: var(--color-bg-darker);
  height: 16px;
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(to right, #ffadad, #ff5757);
  border-radius: 6px;
  transition: width 0.5s ease-out;
  position: relative;
}

.bar-value {
  position: absolute;
  right: 0.5rem;
  top: -1.25rem;
  font-size: 0.8rem;
  color: #ccc;
}
</style>
