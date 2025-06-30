<template>
  <div class="card compact-snapshot">
    <div class="header-row">
      <span class="title">Accounts</span>
      <button class="settings-btn" @click="toggleConfig" :title="showConfig ? 'Done' : 'Configure'">
        <span v-if="showConfig">✓</span>
        <i v-else class="i-carbon-settings"></i>
      </button>
    </div>
    <div v-if="showConfig" class="dropdown-row">
      <FuzzyDropdown :options="accounts" v-model="selectedIds" :max="5" class="w-full" />
    </div>
    <div class="account-list">
      <div v-for="acc in selectedAccounts" :key="acc.account_id" class="account-row">
        <div class="account-info" :title="acc.name">
          <span class="account-name text-ellipsis">{{ acc.name }}</span>
          <span class="account-inst text-xs text-gray-500">{{ acc.institution_name }}</span>
        </div>
        <div class="account-balance">
          <span class="amount">{{ formatCurrency(acc.balance) }}</span>
          <span v-if="reminders[acc.account_id]?.length" class="reminder-badges">
            <span v-for="rem in reminders[acc.account_id]" :key="rem.description + rem.next_due_date" class="badge"
              :title="rem.next_due_date">
              {{ rem.description }}
            </span>
          </span>
        </div>
      </div>
      <div v-if="selectedAccounts.length === 0" class="empty-row">
        No selected accounts.
      </div>
    </div>
    <div class="total-row">
      <span class="label">Total</span>
      <span class="amount total">{{ formatCurrency(totalBalance) }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'

// State & logic
const showConfig = ref(false)
const {
  accounts, selectedAccounts, selectedIds, reminders
} = useSnapshotAccounts()

const toggleConfig = () => {
  showConfig.value = !showConfig.value
}

const totalBalance = computed(() =>
  selectedAccounts.value.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0)
)

function formatCurrency(val) {
  const num = parseFloat(val || 0)
  return num.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
</script>

<style scoped>
@import "../../assets/css/main.css";

.card.compact-snapshot {
  background: var(--color-bg-secondary);
  border-radius: 1rem;
  padding: 1rem;
  box-shadow: var(--shadow-card);
  min-width: 280px;
  max-width: 420px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 1.1rem;
  font-weight: 600;
}

.settings-btn {
  background: none;
  border: none;
  color: var(--color-text-light);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.15em 0.25em;
}

.dropdown-row {
  margin: 0.75rem 0;
}

.account-list {
  margin-top: 0.5rem;
}

.account-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.35rem 0;
  border-bottom: 1px solid #eee;
  gap: 0.5rem;
}

.account-info {
  min-width: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
}

.account-name {
  font-weight: 500;
  max-width: 160px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account-inst {
  font-size: 0.82rem;
  color: #7a7a7a;
}

.account-balance {
  text-align: right;
  min-width: 110px;
  font-family: var(--font-mono, monospace);
  font-weight: 600;
  font-size: 1.02rem;
}

.amount {
  display: inline-block;
  font-variant-numeric: tabular-nums;
}

.reminder-badges {
  margin-left: 0.5em;
  display: inline-flex;
  gap: 2px;
}

.badge {
  background: #f6c;
  color: #fff;
  font-size: 0.7em;
  border-radius: 4px;
  padding: 0 0.35em;
  margin-left: 0.15em;
  vertical-align: middle;
  white-space: nowrap;
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.9rem;
  font-weight: 600;
  font-size: 1.1rem;
  border-top: 1px solid #e6e6e6;
  padding-top: 0.6rem;
}

.total {
  font-size: 1.23em;
  color: var(--color-green, #18a058);
}

.empty-row {
  color: #999;
  font-size: 0.93rem;
  padding: 0.6em 0 0.2em;
  text-align: center;
}

@media (max-width: 600px) {
  .card.compact-snapshot {
    max-width: 99vw;
    padding: 0.7rem;
  }

  .account-name {
    max-width: 80px;
  }

  .account-balance {
    min-width: 70px;
  }
}
</style>
