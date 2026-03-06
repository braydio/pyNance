<template>
  <section class="summary-panel" aria-label="Forecast summary and account selection">
    <div class="summary-header-row">
      <div>
        <h3 class="summary-header">Summary</h3>
        <p class="summary-intro">
          Adjust baseline inputs and choose which accounts contribute to the forecast.
        </p>
      </div>
      <button
        type="button"
        class="selector-toggle"
        :aria-expanded="isSelectorOpen"
        aria-controls="forecast-account-selector"
        @click="isSelectorOpen = !isSelectorOpen"
      >
        {{ isSelectorOpen ? 'Hide account selector' : 'Open account selector' }}
      </button>
    </div>

    <div class="summary-grid">
      <div class="field-group">
        <p class="label">Current Balance</p>
        <button type="button" class="value-link" @click="isSelectorOpen = true">
          ${{ currentBalance.toFixed(2) }}
        </button>
      </div>
      <div class="field-group">
        <label class="label" for="manual-income-input">Manual Income</label>
        <input
          id="manual-income-input"
          type="number"
          class="input"
          :value="localIncome"
          inputmode="decimal"
          @input="emit('update:manualIncome', +$event.target.value)"
        />
      </div>
      <div class="field-group">
        <label class="label" for="liability-rate-input">Liability Rate</label>
        <input
          id="liability-rate-input"
          type="number"
          class="input"
          :value="localRate"
          inputmode="decimal"
          @input="emit('update:liabilityRate', +$event.target.value)"
        />
      </div>
    </div>

    <div v-if="isSelectorOpen" id="forecast-account-selector" class="selector-panel" role="region">
      <p class="selector-title">Account contribution breakdown</p>
      <p class="selector-subtitle">
        Include accounts that should impact the projection. Excluded accounts are omitted from
        baseline calculations.
      </p>

      <div v-if="availableGroupOptions.length > 0" class="group-shortcuts">
        <p class="shortcut-label">Quick select from Dashboard Account Snapshot groups</p>
        <div class="shortcut-list" role="group" aria-label="Account group shortcuts">
          <button
            v-for="group in availableGroupOptions"
            :key="group.id"
            type="button"
            class="chip shortcut-chip"
            :title="groupLabel(group)"
            @click="applyGroupSelection(group.accountIds)"
          >
            {{ groupLabel(group) }}
          </button>
        </div>
      </div>

      <div v-if="accountOptions.length === 0" class="selector-empty">No accounts available.</div>
      <ul v-else class="selector-list" aria-label="Forecast account options">
        <li v-for="account in accountOptions" :key="account.account_id" class="selector-item">
          <div>
            <p class="account-name">{{ account.name }}</p>
            <p class="account-meta">{{ account.institution_name || 'Unknown institution' }}</p>
          </div>
          <div
            class="selector-actions"
            role="group"
            :aria-label="`Selection controls for ${account.name}`"
          >
            <button
              type="button"
              class="chip"
              :class="{ active: isIncluded(account.account_id) }"
              :aria-pressed="isIncluded(account.account_id)"
              @click="toggleIncluded(account.account_id)"
            >
              Include
            </button>
            <button
              type="button"
              class="chip chip-exclude"
              :class="{ active: isExcluded(account.account_id) }"
              :aria-pressed="isExcluded(account.account_id)"
              @click="toggleExcluded(account.account_id)"
            >
              Exclude
            </button>
          </div>
        </li>
      </ul>
    </div>

    <div class="summary-footer">
      <p>
        Net Delta: <strong>{{ netDelta }}</strong>
      </p>
      <p class="summary-selection-copy">
        Included: {{ includedSet.size }} • Excluded: {{ excludedSet.size }}
      </p>
    </div>
  </section>
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
  accountGroupOptions: {
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
const availableGroupOptions = computed(() =>
  (props.accountGroupOptions || []).filter(
    (group) => Array.isArray(group.accountIds) && group.accountIds.length > 0,
  ),
)

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
 * Return a readable label for account-group shortcut chips.
 */
function groupLabel(group) {
  const name = String(group?.name || 'Group').trim() || 'Group'
  const count = Array.isArray(group?.accountIds) ? group.accountIds.length : 0
  return `${name} (${count})`
}

/**
 * Apply a dashboard account-group shortcut to the include/exclude sets.
 */
function applyGroupSelection(accountIds) {
  const ids = Array.isArray(accountIds) ? accountIds : []
  const normalizedIds = ids.map((id) => String(id)).filter(Boolean)
  emit('update:includedAccountIds', normalizedIds)
  emit('update:excludedAccountIds', [])
}

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
  border-radius: 0.75rem;
  border: 1px solid var(--divider);
  box-shadow: 0 1px 2px rgb(15 23 42 / 0.08);
}

.summary-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.summary-header {
  font-size: 1.125rem;
  font-weight: 600;
}

.summary-intro {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.selector-toggle {
  font-size: 0.8rem;
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  padding: 0.4rem 0.7rem;
  background: var(--surface-muted, var(--surface));
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.field-group {
  display: grid;
  gap: 0.35rem;
}

.label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.value-link {
  font-weight: 700;
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  background: var(--surface-muted, var(--surface));
  padding: 0.45rem 0.6rem;
  cursor: pointer;
  color: var(--theme-fg);
  text-align: left;
}

.input {
  width: 100%;
  padding: 0.45rem 0.55rem;
  font-size: 0.9rem;
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  background: var(--input-bg);
  color: var(--theme-fg);
}

.selector-panel {
  margin-top: 0.9rem;
  border-top: 1px solid var(--divider);
  padding-top: 0.85rem;
}

.selector-title {
  font-size: 0.95rem;
  font-weight: 600;
}

.selector-subtitle {
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.group-shortcuts {
  margin-top: 0.75rem;
  padding: 0.6rem;
  border: 1px solid var(--divider);
  border-radius: 0.65rem;
  background: var(--surface-muted, var(--surface));
}

.shortcut-label {
  font-size: 0.78rem;
  color: var(--text-muted);
}

.shortcut-list {
  margin-top: 0.45rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.shortcut-chip {
  font-size: 0.76rem;
}

.selector-list {
  margin-top: 0.7rem;
  list-style: none;
  padding: 0;
  display: grid;
  gap: 0.5rem;
}

.selector-item {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  border: 1px solid var(--divider);
  border-radius: 0.65rem;
  padding: 0.6rem;
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
  padding: 0.3rem 0.55rem;
  border: 1px solid var(--divider);
  border-radius: 999px;
  background: transparent;
  font-size: 0.75rem;
}

.chip.active {
  border-color: var(--color-accent-cyan, #0ea5e9);
  background: var(--brand-soft, #dbeafe);
}

.chip-exclude.active {
  border-color: var(--color-accent-red, #ef4444);
  background: var(--danger-soft, #fee2e2);
}

.summary-footer {
  margin-top: 1rem;
  font-size: 0.9rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.6rem;
}

.summary-selection-copy {
  font-size: 0.8rem;
  color: var(--text-muted);
}
</style>
