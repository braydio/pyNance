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
        <p class="label tooltip-label">
          Assets
          <span class="tooltip-affordance">
            <button type="button" class="tooltip-trigger" aria-label="Explain Assets">?</button>
            <span role="tooltip" class="tooltip-content">
              {{ tooltipCopy.assets }}
            </span>
          </span>
        </p>
        <button type="button" class="value-link" @click="isSelectorOpen = true">
          ${{ assetBalance.toFixed(2) }}
        </button>
      </div>
      <div class="field-group">
        <p class="label tooltip-label">
          Liabilities
          <span class="tooltip-affordance">
            <button type="button" class="tooltip-trigger" aria-label="Explain Liabilities">
              ?
            </button>
            <span role="tooltip" class="tooltip-content">
              {{ tooltipCopy.liabilities }}
            </span>
          </span>
        </p>
        <button type="button" class="value-link" @click="isSelectorOpen = true">
          ${{ liabilityBalance.toFixed(2) }}
        </button>
      </div>
      <div class="field-group">
        <p class="label tooltip-label">
          Current Balance
          <span class="tooltip-affordance">
            <button type="button" class="tooltip-trigger" aria-label="Explain Current Balance">
              ?
            </button>
            <span role="tooltip" class="tooltip-content">
              {{ tooltipCopy.currentBalance }}
            </span>
          </span>
        </p>
        <button type="button" class="value-link" @click="isSelectorOpen = true">
          ${{ netBalance.toFixed(2) }}
        </button>
      </div>
      <div class="field-group">
        <label class="label tooltip-label" for="manual-income-input">
          Manual Income
          <span class="tooltip-affordance">
            <button type="button" class="tooltip-trigger" aria-label="Explain Manual Income">
              ?
            </button>
            <span role="tooltip" class="tooltip-content">
              {{ tooltipCopy.manualIncome }}
            </span>
          </span>
        </label>
        <input
          id="manual-income-input"
          type="number"
          class="input"
          :value="localIncome"
          inputmode="decimal"
          @input="handleManualIncomeInput"
        />
      </div>
      <div class="field-group">
        <label class="label tooltip-label" for="liability-rate-input">
          Liability Rate
          <span class="tooltip-affordance">
            <button type="button" class="tooltip-trigger" aria-label="Explain Liability Rate">
              ?
            </button>
            <span role="tooltip" class="tooltip-content">
              {{ tooltipCopy.liabilityRate }}
            </span>
          </span>
        </label>
        <input
          id="liability-rate-input"
          type="number"
          class="input"
          :value="localRate"
          inputmode="decimal"
          @input="handleLiabilityRateInput"
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
      <p class="tooltip-label">
        Net Delta: <strong>{{ netDelta }}</strong>
        <span class="tooltip-affordance inline-help">
          <button type="button" class="tooltip-trigger" aria-label="Explain Net Delta">?</button>
          <span role="tooltip" class="tooltip-content">
            {{ tooltipCopy.netDelta }}
          </span>
        </span>
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
  assetBalance: {
    type: Number,
    default: 0,
  },
  liabilityBalance: {
    type: Number,
    default: 0,
  },
  netBalance: {
    type: Number,
    default: 0,
  },
  manualIncome: {
    type: Number,
    default: 0,
  },
  liabilityRate: {
    type: Number,
    default: 0,
  },
  netChange: {
    type: Number,
    default: null,
  },
  viewType: {
    type: String,
    default: 'Month',
  },
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
  computeMeta: {
    type: Object,
    default: () => ({}),
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
 * Provide a simple net delta hint based on either compute output or local manual inputs.
 */
const netDelta = computed(() => {
  const fromForecast = Number(props.netChange)
  if (Number.isFinite(fromForecast)) {
    return fromForecast.toFixed(2)
  }
  return ((localIncome.value || 0) - (localRate.value || 0)).toFixed(2)
})

/**
 * Build contextual tooltip copy so the help text stays aligned with current controls.
 */
const tooltipCopy = computed(() => {
  const lookbackDays = Number(props.computeMeta?.lookbackDays ?? 0)
  const movingAverageWindow = Number(props.computeMeta?.movingAverageWindow ?? 0)
  const includesAutoDetectedAdjustments = Boolean(
    props.computeMeta?.includesAutoDetectedAdjustments,
  )
  const autoDetectedAdjustmentCount = Number(props.computeMeta?.autoDetectedAdjustmentCount ?? 0)
  const incomeValue = Number(localIncome.value || 0).toFixed(2)
  const liabilityValue = Number(localRate.value || 0).toFixed(2)
  const forecastScope =
    includedSet.value.size > 0
      ? `${includedSet.value.size} included account${includedSet.value.size === 1 ? '' : 's'}`
      : 'all available forecast accounts'

  return {
    assets: `Assets total the positive-balance accounts currently included in the forecast. Click the amount to review ${forecastScope}.`,
    liabilities: `Liabilities total included debt balances that reduce the starting position. Click the amount to review ${forecastScope}.`,
    currentBalance: `Current Balance is assets minus liabilities across ${forecastScope} before projected cashflow changes are applied.`,
    manualIncome: `Manual Income adds $${incomeValue} per day to the projection in ${props.viewType} view. Use it for steady income not captured automatically.`,
    liabilityRate: `Liability Rate subtracts $${liabilityValue} per day from the projection in ${props.viewType} view and classifies that manual control as debt growth from new spending, not interest accrual.`,
    netDelta: Number.isFinite(Number(props.netChange))
      ? `Net Delta is the forecasted change between the starting and ending balance. It uses a ${movingAverageWindow || 'current'}-day moving average${lookbackDays ? ` across the latest ${lookbackDays} days of history` : ''}${includesAutoDetectedAdjustments ? ` and includes ${autoDetectedAdjustmentCount} auto-detected adjustment${autoDetectedAdjustmentCount === 1 ? '' : 's'}` : ''}.`
      : 'Net Delta falls back to manual income minus liability rate until computed forecast output is available, with the liability control treated as debt growth from new spending.',
  }
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
 * Emit manual income changes using numeric input values.
 */
function handleManualIncomeInput(event) {
  emit('update:manualIncome', Number(event.target?.value || 0))
}

/**
 * Emit manual liability-rate changes using numeric input values.
 */
function handleLiabilityRateInput(event) {
  emit('update:liabilityRate', Number(event.target?.value || 0))
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

.tooltip-label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.tooltip-affordance {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.inline-help {
  margin-left: 0.35rem;
}

.tooltip-trigger {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 1rem;
  height: 1rem;
  border-radius: 9999px;
  border: 1px solid var(--divider);
  background: var(--surface-muted, var(--surface));
  color: var(--text-muted);
  font-size: 0.7rem;
  line-height: 1;
  cursor: help;
}

.tooltip-content {
  position: absolute;
  left: 0;
  top: calc(100% + 0.4rem);
  z-index: 20;
  width: min(18rem, 70vw);
  padding: 0.55rem 0.65rem;
  border-radius: 0.5rem;
  border: 1px solid var(--divider);
  background: var(--surface);
  color: var(--theme-fg);
  box-shadow: 0 10px 25px rgb(15 23 42 / 0.12);
  font-size: 0.75rem;
  line-height: 1.4;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-0.2rem);
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

.tooltip-affordance:hover .tooltip-content,
.tooltip-affordance:focus-within .tooltip-content {
  opacity: 1;
  transform: translateY(0);
}

.value-link {
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--theme-fg);
  text-align: left;
  font-size: 1.15rem;
  font-weight: 600;
  cursor: pointer;
}

.input {
  width: 100%;
}

.selector-panel {
  margin-top: 1rem;
  border-top: 1px solid var(--divider);
  padding-top: 1rem;
}

.selector-title {
  font-weight: 600;
}

.selector-subtitle,
.summary-selection-copy,
.selector-empty,
.account-meta,
.shortcut-label {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.group-shortcuts {
  margin-top: 0.75rem;
  display: grid;
  gap: 0.45rem;
}

.shortcut-list,
.selector-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.selector-list {
  list-style: none;
  padding: 0;
  margin: 0.75rem 0 0;
  display: grid;
  gap: 0.75rem;
}

.selector-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem;
  border: 1px solid var(--divider);
  border-radius: 0.65rem;
}

.account-name {
  font-weight: 600;
}

.chip {
  border: 1px solid var(--divider);
  border-radius: 999px;
  padding: 0.35rem 0.7rem;
  background: var(--surface-muted, var(--surface));
  font-size: 0.8rem;
}

.chip.active {
  border-color: var(--accent, #2563eb);
  color: var(--accent, #2563eb);
}

.chip-exclude.active {
  border-color: #dc2626;
  color: #dc2626;
}

.summary-footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 1rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--divider);
  flex-wrap: wrap;
}
</style>
