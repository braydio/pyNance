<template>
  <div class="summary-panel">
    <div class="summary-header-row">
      <h3 class="summary-header">Summary</h3>
      <button type="button" class="selector-toggle" @click="isSelectorOpen = !isSelectorOpen">
        {{ isSelectorOpen ? 'Hide account selector' : 'Select accounts' }}
      </button>
    </div>

    <div class="summary-grid">
      <div>
        <p class="label">Current Balance</p>
        <button type="button" class="value-link" @click="isSelectorOpen = true">
          ${{ currentBalance.toFixed(2) }}
        </button>
      </div>
      <div>
        <p class="label">Manual Income</p>
        <input
          type="number"
          class="input"
          :value="localIncome"
          @input="emit('update:manualIncome', +$event.target.value)"
        />
      </div>
      <div>
        <p class="label">Liability Rate</p>
        <input
          type="number"
          class="input"
          :value="localRate"
          @input="emit('update:liabilityRate', +$event.target.value)"
        />
      </div>
    </div>

    <div v-if="isSelectorOpen" class="selector-panel">
      <p class="selector-title">Account contribution breakdown</p>
      <p class="selector-subtitle">
        Toggle included/excluded accounts to recalculate the forecast baseline.
      </p>

      <div v-if="accountOptions.length === 0" class="selector-empty">No accounts available.</div>
      <div v-else class="selector-list">
        <div v-for="account in accountOptions" :key="account.account_id" class="selector-item">
          <div>
            <p class="account-name">{{ account.name }}</p>
            <p class="account-meta">{{ account.institution_name || 'Unknown institution' }}</p>
          </div>
          <div class="selector-actions">
            <button
              type="button"
              class="chip"
              :class="{ active: isIncluded(account.account_id) }"
              @click="toggleIncluded(account.account_id)"
            >
              Include
            </button>
            <button
              type="button"
              class="chip chip-exclude"
              :class="{ active: isExcluded(account.account_id) }"
              @click="toggleExcluded(account.account_id)"
            >
              Exclude
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="summary-footer">
      <p>
        Net Delta: <strong>{{ netDelta }}</strong>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, toRef } from 'vue'

const props = defineProps({
  currentBalance: Number,
  manualIncome: Number,
  liabilityRate: Number,
  netChange: {
    type: Number,
    default: null,
  },
  viewType: String,
  accountOptions: {
    type: Array,
    default: () => [],
  },
  includedAccountIds: {
    type: Array,
    default: () => [],
  },
  excludedAccountIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits([
  'update:manualIncome',
  'update:liabilityRate',
  'update:includedAccountIds',
  'update:excludedAccountIds',
])

const localIncome = toRef(props, 'manualIncome')
const localRate = toRef(props, 'liabilityRate')
const isSelectorOpen = ref(false)

const includedSet = computed(() => new Set(props.includedAccountIds || []))
const excludedSet = computed(() => new Set(props.excludedAccountIds || []))

/**
 * Provide a simple net delta hint based on manual adjustments.
 */
const netDelta = computed(() => {
  const fromForecast = Number(props.netChange)
  if (Number.isFinite(fromForecast)) {
    return fromForecast.toFixed(2)
  }
  return ((localIncome.value || 0) - (localRate.value || 0)).toFixed(2)
})

/**
 * Return whether an account is currently included in compute requests.
 */
function isIncluded(accountId) {
  return includedSet.value.has(accountId)
}

/**
 * Return whether an account is currently excluded from compute requests.
 */
function isExcluded(accountId) {
  return excludedSet.value.has(accountId)
}

/**
 * Toggle account inclusion and ensure exclusion list stays mutually exclusive.
 */
function toggleIncluded(accountId) {
  const nextIncluded = new Set(includedSet.value)
  const nextExcluded = new Set(excludedSet.value)
  if (nextIncluded.has(accountId)) {
    nextIncluded.delete(accountId)
  } else {
    nextIncluded.add(accountId)
    nextExcluded.delete(accountId)
  }
  emit('update:includedAccountIds', Array.from(nextIncluded))
  emit('update:excludedAccountIds', Array.from(nextExcluded))
}

/**
 * Toggle account exclusion and ensure inclusion list stays mutually exclusive.
 */
function toggleExcluded(accountId) {
  const nextIncluded = new Set(includedSet.value)
  const nextExcluded = new Set(excludedSet.value)
  if (nextExcluded.has(accountId)) {
    nextExcluded.delete(accountId)
  } else {
    nextExcluded.add(accountId)
    nextIncluded.delete(accountId)
  }
  emit('update:includedAccountIds', Array.from(nextIncluded))
  emit('update:excludedAccountIds', Array.from(nextExcluded))
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
.summary-panel {
  background: var(--surface);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
}

.summary-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.summary-header {
  font-size: 1.125rem;
  font-weight: 600;
}

.selector-toggle {
  font-size: 0.8rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}

.label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.value-link {
  font-weight: bold;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  color: var(--theme-fg);
}

.input {
  width: 100%;
  padding: 0.4rem;
  font-size: 0.9rem;
  border: 1px solid var(--divider);
  border-radius: 0.375rem;
  background: var(--input-bg);
  color: var(--theme-fg);
}

.selector-panel {
  margin-top: 0.75rem;
  border-top: 1px solid var(--divider);
  padding-top: 0.75rem;
}

.selector-title {
  font-size: 0.95rem;
  font-weight: 600;
}

.selector-subtitle {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.selector-list {
  margin-top: 0.5rem;
  display: grid;
  gap: 0.5rem;
}

.selector-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}

.account-name {
  font-size: 0.9rem;
  font-weight: 500;
}

.account-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.selector-actions {
  display: flex;
  gap: 0.35rem;
}

.chip {
  padding: 0.25rem 0.5rem;
  border: 1px solid var(--divider);
  border-radius: 999px;
  background: transparent;
  font-size: 0.75rem;
}

.chip.active {
  background: var(--brand-soft, #dbeafe);
}

.chip-exclude.active {
  background: var(--danger-soft, #fee2e2);
}

.summary-footer {
  margin-top: 1rem;
  font-size: 0.9rem;
}
</style>
