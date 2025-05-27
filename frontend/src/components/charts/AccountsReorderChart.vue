<template>
  <div class="chart-container card">
    <h2 class="heading-md">Top {{ accountSubtype }} Accounts</h2>

    <div v-if="filteredAccounts.length" class="bar-chart">
      <div
        v-for="account in filteredAccounts"
        :key="account.id"
        class="bar-row"
      >
        <span class="bar-label">{{ account.name }}</span>
        <div class="bar-outer">
          <div
            class="bar-fill"
            :style="{ width: barWidth(account) }"
          >
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <p v-else class="no-data-msg">No accounts available for this subtype.</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({ accountSubtype: String })

const accounts = ref([])
const loading = ref(true)

const format = val => new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
}).format(val)

const barWidth = (account) => {
  const max = Math.max(...filteredAccounts.value.map(a => Math.abs(a.adjusted_balance)), 1)
  return `${(Math.abs(account.adjusted_balance) / max) * 100}%`
}

const filteredAccounts = computed(() =>
  accounts.value
    .filter(a => a.subtype?.toLowerCase() === props.accountSubtype.toLowerCase())
    .sort((a, b) => b.adjusted_balance - a.adjusted_balance)
    .slice(0, 5)
)

const fetchAccounts = async () => {
  try {
    const { data } = await axios.get('/api/accounts/get_accounts')
    if (data?.status === 'success') {
      accounts.value = data.accounts.map(acc => ({
        ...acc,
        adjusted_balance: Math.abs(acc.balance ?? 0),
      }))
    }
  } catch (err) {
    console.error('Failed to load accounts:', err)
  } finally {
    loading.value = false
  }
}

onMounted(fetchAccounts)
</script>


<style scoped>
.chart-container {
  padding: 1rem 1.25rem;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.bar-label {
  flex: 1;
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-outer {
  flex: 4;
  background: var(--color-bg-dark);
  border-radius: 6px;
  height: 14px;
  position: relative;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(to right, #aad4ff, #78baff);
  border-radius: 6px;
  transition: width 0.6s ease-out;
  position: relative;
}

.bar-value {
  position: absolute;
  right: 0.5rem;
  top: -1.5rem;
  font-size: 0.8rem;
  color: #ccd;
}

.no-data-msg {
  text-align: center;
  font-style: italic;
  color: var(--color-text-muted);
  padding: 1rem 0.5rem;
}
</style>
