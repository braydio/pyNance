<template>
  <section class="summary-panel" aria-label="Forecast summary and account selection">
    <div class="summary-header-row">
      <div>
        <h3 class="summary-header">Where you're headed</h3>
        <p class="summary-lead" data-testid="summary-lead">
          Net change over this horizon: <strong>{{ netDelta }}</strong> · {{ includedSet.size }}
          accounts included
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

    <div v-if="isV2 && liquidity" class="liquidity-summary" data-testid="liquidity-summary">
      <dl class="liquidity-grid">
        <div class="liquidity-cell">
          <dt>Cash today</dt>
          <dd data-testid="cash-today">{{ money(liquidity.starting_cash) }}</dd>
        </div>
        <div class="liquidity-cell">
          <dt>Cash at end</dt>
          <dd data-testid="cash-end">{{ money(liquidity.ending_cash) }}</dd>
        </div>
        <div class="liquidity-cell">
          <dt>Lowest cash</dt>
          <dd data-testid="cash-min">
            {{ money(liquidity.min_cash) }}
            <span class="liquidity-muted">on {{ liquidity.min_cash_date }}</span>
          </dd>
        </div>
        <div class="liquidity-cell">
          <dt>Projected shortfall</dt>
          <dd data-testid="shortfall" :class="{ 'liquidity-warn': liquidity.first_shortfall_date }">
            {{ shortfallCopy }}
          </dd>
        </div>
      </dl>
      <p v-if="uncertainty?.available" class="risk-copy" data-testid="risk-copy">
        Simulated chance cash drops below $0 on any day:
        <strong>{{ percent(uncertainty.risk_below_zero_any_day) }}</strong
        >; below {{ money(uncertainty.threshold ?? 0) }}:
        <strong>{{ percent(uncertainty.risk_below_threshold_any_day) }}</strong>
        ({{ uncertainty.sample_count }} simulations, a model estimate, not a guarantee).
      </p>
      <p v-else class="risk-copy" data-testid="risk-unavailable">
        {{ uncertaintyUnavailableCopy }}
      </p>
      <div v-if="netWorth" class="debt-coverage" data-testid="debt-coverage">
        <p class="liquidity-muted" data-testid="debt-outstanding">
          Outstanding debt tracked separately: {{ money(netWorth.liabilities.starting) }}. This is
          what you owe, not a cash event.
        </p>
        <p class="liquidity-muted" data-testid="debt-payments-included">
          {{ debtPaymentsCopy }}
        </p>
        <p
          class="liquidity-muted"
          :class="{ 'debt-coverage__caution': debtCoverageMode !== 'settlement' }"
          data-testid="debt-coverage-status"
        >
          {{ debtCoverageCopy }}
        </p>
        <p class="liquidity-muted" data-testid="net-worth-note">
          Investments {{ money(netWorth.investments.starting) }} and net worth
          {{ money(netWorth.starting) }} are shown separately and are not part of this cash
          forecast.
        </p>
      </div>
    </div>

    <p v-if="!isV2" class="liquidity-muted" data-testid="v1-debt-note">
      Debt totals are separate from modeled bank cash.
    </p>

    <div v-if="!isV2" class="summary-grid">
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
          {{ money(assetBalance) }}
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
          {{ money(liabilityBalance) }}
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
          {{ money(netBalance) }}
        </button>
      </div>
    </div>

    <details class="manual-inputs" data-testid="manual-inputs">
      <summary class="manual-inputs__summary">Manual baseline inputs</summary>
      <p id="manual-inputs-note" class="manual-inputs__note">
        Both values are dollars per day, not percentages, and apply to the forecast as you type.
      </p>
      <div class="summary-grid">
        <div class="field-group">
          <label class="label tooltip-label" for="manual-income-input">
            Manual Income ($ per day)
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
            aria-describedby="manual-inputs-note"
            :value="localIncome"
            inputmode="decimal"
            @input="handleManualIncomeInput"
          />
        </div>
        <div class="field-group">
          <label class="label tooltip-label" for="liability-rate-input">
            Liability Rate ($ per day)
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
            aria-describedby="manual-inputs-note"
            :value="localRate"
            inputmode="decimal"
            @input="handleLiabilityRateInput"
          />
        </div>
      </div>
    </details>

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
import { formatForecastMoney, formatSignedCashflow } from '@/utils/format'

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
  modelVersion: {
    type: String,
    default: 'v1',
  },
  liquidity: {
    type: Object,
    default: null,
  },
  uncertainty: {
    type: Object,
    default: null,
  },
  netWorth: {
    type: Object,
    default: null,
  },
  /** Additive `metadata.debt_payment_coverage` from the V2 forecast. */
  debtPaymentCoverage: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits([
  'update:manualIncome',
  'update:liabilityRate',
  'update:includedAccountIds',
  'update:excludedAccountIds',
])

const isV2 = computed(() => props.modelVersion === 'v2')
// Missing data reads "Unavailable", never $0.00.
const money = formatForecastMoney
const percent = (value) => `${Math.round(Number(value ?? 0) * 100)}%`
const shortfallCopy = computed(() =>
  props.liquidity?.first_shortfall_date
    ? `Cash goes below $0 on ${props.liquidity.first_shortfall_date}`
    : 'No shortfall projected',
)
const uncertaintyUnavailableCopy = computed(() => {
  const reason = String(props.uncertainty?.reason ?? '')
  if (reason === 'simulation_disabled') return 'Probability estimates are turned off.'
  if (reason.startsWith('insufficient_history'))
    return 'Not enough clean history yet to estimate a range or shortfall probability.'
  return 'A range and shortfall probability are not available for this forecast.'
})

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
  if (props.netChange !== null && Number.isFinite(fromForecast)) {
    return formatSignedCashflow(fromForecast)
  }
  return formatSignedCashflow((localIncome.value || 0) - (localRate.value || 0))
})

const debtCoverageMode = computed(() => props.debtPaymentCoverage?.mode ?? 'proxy')

/** Scheduled debt payments that actually reduce cash in this forecast, and how many plans they come from. */
const debtPaymentsCopy = computed(() => {
  const included = props.debtPaymentCoverage?.included ?? []
  const streams = new Set(included.map((payment) => payment.stream_id))
  const total = included.reduce((sum, payment) => sum + Number(payment.amount || 0), 0)
  if (!included.length) {
    return 'Scheduled debt payments included: none. No verified payment plan reduces cash in this forecast.'
  }
  return `Scheduled debt payments included: ${money(total)} across ${streams.size} verified ${streams.size === 1 ? 'stream' : 'streams'}.`
})

const debtCoverageCopy = computed(() => {
  const coverage = props.debtPaymentCoverage
  if (!coverage) return 'Other debt payment coverage: unverified.'
  if (coverage.mode === 'settlement') {
    return 'Debt payment coverage: every tracked card and loan has a verified payment plan.'
  }
  const unmodeled = Number(coverage.unmodeled_account_count || 0)
  const noun = unmodeled === 1 ? 'account has' : 'accounts have'
  if (coverage.mode === 'mixed') {
    return `Other debt payment coverage: incomplete. ${unmodeled} ${noun} no verified payment plan, so card purchases there still count as cash spending.`
  }
  return 'Other debt payment coverage: unverified. Card purchases are counted as cash spending until a payment plan is confirmed.'
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
  const incomeValue = formatForecastMoney(Number(localIncome.value || 0))
  const liabilityValue = formatForecastMoney(Number(localRate.value || 0))
  const forecastScope =
    includedSet.value.size > 0
      ? `${includedSet.value.size} included account${includedSet.value.size === 1 ? '' : 's'}`
      : 'all available forecast accounts'

  return {
    assets: `Assets total the positive-balance accounts currently included in the forecast. Click the amount to review ${forecastScope}.`,
    liabilities: `Liabilities total included debt balances that reduce the starting position. Click the amount to review ${forecastScope}.`,
    currentBalance: `Current Balance is assets minus liabilities across ${forecastScope} before projected cashflow changes are applied.`,
    manualIncome: `Manual Income adds ${incomeValue} per day to the projection in ${props.viewType} view. Use it for steady income not captured automatically.`,
    liabilityRate: `Liability Rate subtracts ${liabilityValue} per day from the projection in ${props.viewType} view to model recurring debt growth or payments.`,
    netDelta: Number.isFinite(Number(props.netChange))
      ? `Net Delta is the forecasted change between the starting and ending balance. It uses a ${movingAverageWindow || 'current'}-day moving average${lookbackDays ? ` across the latest ${lookbackDays} days of history` : ''}${includesAutoDetectedAdjustments ? ` and includes ${autoDetectedAdjustmentCount} auto-detected adjustment${autoDetectedAdjustmentCount === 1 ? '' : 's'}` : ''}.`
      : 'Net Delta falls back to manual income minus liability rate until computed forecast output is available.',
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
.summary-lead {
  font-size: 1.1rem;
}

.manual-inputs__note {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.manual-inputs__summary {
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

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
  flex-wrap: wrap;
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
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.selector-toggle {
  font-size: 0.8125rem;
  border: 1px solid var(--divider);
  border-radius: 0.5rem;
  padding: 0.4rem 0.7rem;
  background: var(--surface-muted, var(--surface));
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 11.25rem), 1fr));
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

.liquidity-summary {
  display: grid;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.liquidity-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: 0.75rem;
  margin: 0;
}

.liquidity-cell dt {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.liquidity-cell dd {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
}

.liquidity-muted {
  font-size: 0.8125rem;
  font-weight: 400;
  color: var(--text-muted);
}

.debt-coverage {
  display: grid;
  gap: 0.25rem;
}

.debt-coverage p {
  margin: 0;
}

.debt-coverage__caution {
  color: var(--color-text-light);
  padding-left: 0.6rem;
  border-left: 3px solid color-mix(in srgb, var(--color-warning) 70%, transparent);
}

.liquidity-warn {
  color: var(--text-negative);
}

.risk-copy {
  font-size: 0.875rem;
  margin: 0;
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
  font-size: 0.8125rem;
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
  font-size: 0.8125rem;
  line-height: 1.4;
  opacity: 0;
  pointer-events: none;
  transform: translateY(-0.2rem);
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}

/* Below xl the panel is the positioning context so hidden tooltips cannot widen the page. */
@media (max-width: 1279px) {
  .summary-panel {
    position: relative;
  }

  .tooltip-affordance {
    position: static;
  }

  .tooltip-content {
    left: 0;
    top: auto;
    margin-top: 0.4rem;
    width: min(18rem, calc(100% - 1rem));
  }
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
  font-size: 0.8125rem;
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
  font-size: 0.8125rem;
}

.chip.active {
  border-color: var(--accent-primary);
  color: var(--text-link);
}

.chip-exclude.active {
  border-color: var(--text-negative);
  color: var(--text-negative);
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
