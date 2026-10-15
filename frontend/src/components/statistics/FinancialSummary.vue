<!--
  FinancialSummary.vue
  Collapsible financial detail panel for the dashboard. Collapsed it is a quiet
  entry row; expanded it reads: date context, upcoming recurring (next 7 days
  from today), selected-day spending, period net cash flow, then a closed
  "More statistics" section. Unusual days emit `select-date` so the parent can
  open the existing date transaction modal.
-->
<template>
  <div class="statistics-container">
    <!-- Collapsed row: a quiet entry point, not another income/expense/net hero -->
    <div class="stats-header">
      <div class="stats-heading">
        <h3 class="stats-title">Financial details</h3>
        <p v-if="periodLabel" class="stats-period">{{ periodLabel }}</p>
      </div>
      <div class="stats-controls">
        <button
          type="button"
          class="accent-toggle-btn"
          :class="{ 'accent-toggle-btn--active': isExtendedView }"
          :aria-expanded="isExtendedView ? 'true' : 'false'"
          aria-controls="financial-details-panel"
          @click="toggleExtendedView"
        >
          {{ isExtendedView ? 'Hide details' : 'Show details' }}
        </button>
      </div>
    </div>

    <Transition name="expand">
      <div v-if="isExtendedView" id="financial-details-panel" class="extended-stats">
        <!-- 1. Date context -->
        <div class="detail-date-controls">
          <label class="detail-date-label" for="financial-snapshot-detail-date"
            >View snapshot as of</label
          >
          <input
            id="financial-snapshot-detail-date"
            v-model="detailDate"
            :max="maxDetailDate"
            :min="minDetailDate"
            type="date"
            class="detail-date-input"
          />
          <button
            v-if="shouldShowResetButton"
            type="button"
            class="detail-date-reset"
            @click="resetDetailDate"
          >
            Reset to today
          </button>
          <p class="detail-date-helper">Activity through {{ viewingDateLabel }}</p>
        </div>

        <!-- 2. Upcoming recurring (always relative to today, not detailDate) -->
        <section
          class="recurring-upcoming-panel"
          aria-labelledby="recurring-upcoming-title"
          aria-live="polite"
        >
          <div class="recurring-upcoming-header">
            <h4 id="recurring-upcoming-title" class="group-title mb-0">Due in the next 7 days</h4>
            <p class="recurring-upcoming-subtitle">As of today, {{ todayLabel }}</p>
          </div>
          <p v-if="isLoadingRecurring" class="recurring-upcoming-state">
            Loading upcoming recurring transactions…
          </p>
          <template v-else>
            <p v-if="recurringStatus === 'no-accounts'" class="recurring-upcoming-state">
              No accounts are selected for the dashboard snapshot, so nothing can be checked.
            </p>
            <div v-else-if="recurringStatus === 'error'" class="recurring-upcoming-state">
              <p class="recurring-upcoming-message" role="alert">
                Unable to load upcoming recurring transactions.
              </p>
              <button type="button" class="recurring-upcoming-retry" @click="retryRecurring">
                Retry
              </button>
            </div>
            <template v-else>
              <p v-if="recurringFailedCount > 0" class="recurring-upcoming-warning" role="status">
                Couldn't check {{ recurringFailedCount }} of {{ recurringAccountCount }} accounts;
                this list may be incomplete.
                <button type="button" class="recurring-upcoming-retry" @click="retryRecurring">
                  Retry
                </button>
              </p>
              <p v-if="!upcomingReminders.length" class="recurring-upcoming-state">
                No recurring items due in the next 7 days.
              </p>
              <ul v-else class="recurring-upcoming-list">
                <li
                  v-for="(reminder, index) in visibleReminders"
                  :key="buildReminderKey(reminder, index)"
                  class="recurring-upcoming-item"
                >
                  <div>
                    <div class="recurring-upcoming-description">{{ reminder.description }}</div>
                    <div class="recurring-upcoming-meta">
                      {{ describeDue(reminder) }} ·
                      {{ reminder.source === 'user' ? 'Scheduled' : 'Likely recurring' }}
                      <template
                        v-if="reminder.source !== 'user' && reminder.auto_detection.occurrences"
                      >
                        · based on {{ reminder.auto_detection.occurrences }} matches
                      </template>
                    </div>
                  </div>
                  <div class="recurring-upcoming-amount">{{ reminder.amount }}</div>
                </li>
              </ul>
              <p v-if="hiddenReminderCount > 0" class="recurring-upcoming-more">
                +{{ hiddenReminderCount }} more due in 7 days
              </p>
            </template>
          </template>
          <router-link class="recurring-upcoming-link" to="/transactions"
            >View transactions</router-link
          >
        </section>

        <!-- 3. Selected-day spending + latest transactions -->
        <DailySpendingPanel :detail-date="detailDate" :min-detail-date="minDetailDate" />

        <!-- 4. Period interpretation -->
        <section class="period-summary" aria-labelledby="period-summary-title">
          <h4 id="period-summary-title" class="group-title">
            Period through {{ viewingDateLabel }}
          </h4>
          <div class="period-summary-grid">
            <div class="stat-item stat-net" :class="netPolarityClass">
              <span class="stat-label">Net cash flow:</span>
              <span class="stat-value" :class="amountPolarityClass(detailSummary.totalNet)">{{
                formatAmount(detailSummary.totalNet)
              }}</span>
            </div>
            <div class="stat-item stat-income">
              <span class="stat-label">Income:</span>
              <span class="stat-value" :class="amountPolarityClass(detailSummary.totalIncome)">{{
                formatAmount(detailSummary.totalIncome)
              }}</span>
            </div>
            <div class="stat-item stat-expenses">
              <span class="stat-label">Expenses:</span>
              <span class="stat-value" :class="amountPolarityClass(detailSummary.totalExpenses)">{{
                formatAmount(detailSummary.totalExpenses)
              }}</span>
            </div>
            <div v-if="netPercentOfIncomeLabel" class="stat-item stat-net-percent">
              <span class="stat-label">Net as % of income:</span>
              <span class="stat-value">{{ netPercentOfIncomeLabel }}</span>
            </div>
          </div>
        </section>

        <!-- 5. Secondary statistics, closed by default -->
        <details class="more-statistics">
          <summary>More statistics</summary>
          <p class="more-statistics-note">
            Based on {{ dayCountLabel }}. Days with no activity count as zero in daily averages and
            day counts.
          </p>
          <div class="stats-grid">
            <div class="stat-group">
              <h4 class="group-title">Daily averages</h4>
              <div class="stat-item">
                <span class="stat-label">Income:</span>
                <span
                  class="stat-value"
                  :class="amountPolarityClass(extendedMetrics.avgDailyIncome)"
                  >{{ formatAmount(extendedMetrics.avgDailyIncome) }}</span
                >
              </div>
              <div class="stat-item">
                <span class="stat-label">Expenses:</span>
                <span
                  class="stat-value"
                  :class="amountPolarityClass(extendedMetrics.avgDailyExpenses)"
                  >{{ formatAmount(extendedMetrics.avgDailyExpenses) }}</span
                >
              </div>
              <div class="stat-item">
                <span class="stat-label">Net:</span>
                <span
                  class="stat-value"
                  :class="amountPolarityClass(extendedMetrics.avgDailyNet)"
                  >{{ formatAmount(extendedMetrics.avgDailyNet) }}</span
                >
              </div>
              <div class="stat-item stat-ma7">
                <span class="stat-label">Last 7 days, average net:</span>
                <span class="stat-value" :class="amountPolarityClass(extendedMetrics.netMA7)">{{
                  movingAverageLabel(extendedMetrics.netMA7, 7)
                }}</span>
              </div>
              <div class="stat-item stat-ma30">
                <span class="stat-label">Last 30 days, average net:</span>
                <span class="stat-value" :class="amountPolarityClass(extendedMetrics.netMA30)">{{
                  movingAverageLabel(extendedMetrics.netMA30, 30)
                }}</span>
              </div>
            </div>

            <div class="stat-group">
              <h4 class="group-title">First vs last day (not a period trend)</h4>
              <div class="stat-item">
                <span class="stat-label">Net:</span>
                <span
                  class="stat-value trend-indicator"
                  :class="amountPolarityClass(extendedMetrics.netChange)"
                  >{{ formatCurrencyDelta(extendedMetrics.netChange) }}</span
                >
              </div>
              <div class="stat-item">
                <span class="stat-label">Income:</span>
                <span
                  class="stat-value trend-indicator"
                  :class="amountPolarityClass(extendedMetrics.incomeChange)"
                  >{{ formatCurrencyDelta(extendedMetrics.incomeChange) }}</span
                >
              </div>
              <div class="stat-item">
                <span class="stat-label">Expenses:</span>
                <span
                  class="stat-value trend-indicator"
                  :class="amountPolarityClass(extendedMetrics.expenseChange)"
                  >{{ formatCurrencyDelta(extendedMetrics.expenseChange) }}</span
                >
              </div>
              <div class="stat-item">
                <span class="stat-label">Daily net standard deviation:</span>
                <span class="stat-value">{{ formatAmount(extendedMetrics.volatility) }}</span>
              </div>
            </div>

            <div class="stat-group">
              <h4 class="group-title">Largest days</h4>
              <div class="stat-item">
                <span class="stat-label">Income:</span>
                <span class="stat-value outlier-value">
                  <span>{{ topEarningDateLabel }}</span>
                  <span
                    class="outlier-amount"
                    :class="amountPolarityClass(topEarningAmountValue)"
                    >{{ topEarningAmountLabel }}</span
                  >
                </span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Expense:</span>
                <span class="stat-value outlier-value">
                  <span>{{ topSpendingDateLabel }}</span>
                  <span
                    class="outlier-amount"
                    :class="amountPolarityClass(topSpendingAmountValue)"
                    >{{ topSpendingAmountLabel }}</span
                  >
                </span>
              </div>
              <div class="stat-item stat-unusual">
                <span class="stat-label">Unusual days:</span>
                <span v-if="unusualDays.length" class="stat-value unusual-days">
                  <button
                    v-for="date in unusualDays"
                    :key="date"
                    type="button"
                    class="unusual-day-btn"
                    @click="emit('select-date', date)"
                  >
                    {{ date }}
                  </button>
                </span>
                <span v-else class="stat-value">{{ unusualDaysEmptyLabel }}</span>
              </div>
            </div>

            <div class="stat-group">
              <h4 class="group-title">Day counts</h4>
              <div class="stat-item">
                <span class="stat-label">Positive-net days:</span>
                <span class="stat-value">{{ positiveDaysLabel }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Negative-net days:</span>
                <span class="stat-value">{{ negativeDaysLabel }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Average positive-net day:</span>
                <span class="stat-value" :class="amountPolarityClass(avgPositiveNetDayValue)">{{
                  avgPositiveNetDayLabel
                }}</span>
              </div>
            </div>
          </div>
        </details>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import api from '@/services/api'
import { getRecurringTransactions } from '@/api/recurring'
import { amountPolarityClass, formatAmount } from '@/utils/format'
import DailySpendingPanel from './DailySpendingPanel.vue'

/** Minimum days of history before moving averages / unusual days are meaningful. */
const MIN_OUTLIER_SAMPLE_DAYS = 7
const MAX_UNUSUAL_DAYS = 3
const MAX_VISIBLE_REMINDERS = 6
const RECURRING_TTL_MS = 5 * 60 * 1000

/**
 * Format a numeric delta with shared accounting-style currency rules.
 *
 * @param {number} value - The value to format.
 * @returns {string} Accounting-style currency string.
 */
function formatCurrencyDelta(value) {
  return formatAmount(value)
}

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      totalIncome: 0,
      totalExpenses: 0,
      totalNet: 0,
      highestIncomeDay: null,
      highestExpenseDay: null,
      trend: 0,
      volatility: 0,
      outlierDates: [],
    }),
  },
  chartData: {
    type: Array,
    default: () => [],
  },
  zoomedOut: {
    type: Boolean,
    default: false,
  },
  startDate: {
    type: String,
    default: '',
  },
  endDate: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['select-date'])

// Toggle state for basic/extended view
const isExtendedView = ref(false)

function toggleExtendedView() {
  isExtendedView.value = !isExtendedView.value
}

const TODAY = new Date()
const TODAY_ISO = formatAsISODate(TODAY)

const detailDate = ref(TODAY_ISO)
const userAdjustedDate = ref(false)

const chartDateBounds = computed(() => {
  const data = Array.isArray(props.chartData) ? props.chartData : []
  const sortedDates = data
    .map((entry) => entry?.date)
    .concat([props.startDate, props.endDate])
    .filter((date) => Boolean(parseISODate(date)))
    .sort()

  return {
    min: sortedDates[0] || '',
    max: sortedDates[sortedDates.length - 1] || '',
  }
})

const minDetailDate = computed(() => chartDateBounds.value.min)
const maxDetailDate = computed(() => chartDateBounds.value.max || TODAY_ISO)

/**
 * Compute the default detail date (today clamped within available bounds).
 */
const defaultDetailDate = computed(() =>
  clampDateString(TODAY_ISO, minDetailDate.value, maxDetailDate.value),
)

const shouldShowResetButton = computed(() => detailDate.value !== defaultDetailDate.value)

watch(
  chartDateBounds,
  (bounds) => {
    if (!bounds.max) {
      detailDate.value = TODAY_ISO
      return
    }
    const target = userAdjustedDate.value ? detailDate.value : defaultDetailDate.value
    detailDate.value = clampDateString(target, bounds.min, bounds.max)
  },
  { immediate: true },
)

watch(detailDate, (value, oldValue) => {
  if (value === oldValue) {
    return
  }
  if (!value) {
    detailDate.value = defaultDetailDate.value
    return
  }
  userAdjustedDate.value = value !== defaultDetailDate.value
})

/**
 * Reset the detail snapshot view back to today's date (bounded by data).
 */
function resetDetailDate() {
  userAdjustedDate.value = false
  detailDate.value = defaultDetailDate.value
}

/**
 * Format an ISO date as a short locale label (e.g. "Apr 11").
 *
 * @param {string} iso - ISO date string.
 * @returns {string} Short label, or the input when unparseable.
 */
function formatShortDate(iso) {
  const parsed = parseISODate(iso)
  return parsed ? parsed.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : iso
}

const periodLabel = computed(() => {
  if (!props.startDate || !props.endDate) return ''
  return `Selected period: ${formatShortDate(props.startDate)} – ${formatShortDate(props.endDate)}`
})

const todayLabel = computed(() => formatShortDate(TODAY_ISO))

// ---------------------------------------------------------------------------
// Upcoming recurring (due-first, coverage-aware). Always relative to today.
// ---------------------------------------------------------------------------

const upcomingReminders = ref([])
const isLoadingRecurring = ref(false)
/** @type {import('vue').Ref<'idle'|'ok'|'no-accounts'|'error'>} */
const recurringStatus = ref('idle')
const recurringFailedCount = ref(0)
const recurringAccountCount = ref(0)
let recurringFetchedAt = 0
let recurringRequestId = 0
let isUnmounted = false

const visibleReminders = computed(() => upcomingReminders.value.slice(0, MAX_VISIBLE_REMINDERS))
const hiddenReminderCount = computed(() =>
  Math.max(0, upcomingReminders.value.length - MAX_VISIBLE_REMINDERS),
)

/**
 * Build a stable key for rendering recurring reminders.
 *
 * @param {Record<string, unknown>} reminder - Reminder payload from recurring endpoints.
 * @param {number} index - Position in the deterministic sort order.
 * @returns {string} Key for list rendering.
 */
function buildReminderKey(reminder, index) {
  return `${reminder.account_id}-${reminder.source}-${reminder.description}-${reminder.next_due_date}-${reminder.amount}-${index}`
}

/**
 * Normalize a reminder payload with deterministic fallback confidence.
 *
 * @param {Record<string, unknown>} reminder - Raw reminder response item.
 * @param {string} accountId - Account identifier that produced the reminder.
 * @returns {Record<string, unknown>} Reminder augmented with sorting metadata.
 */
function normalizeReminder(reminder, accountId) {
  const occurrences = Number(reminder?.auto_detection?.occurrences ?? 0)
  const serverConfidence = Number(reminder?.auto_detection?.confidence_score)
  const fallbackConfidence =
    (reminder?.source === 'auto' ? 40 : 20) + Math.min(occurrences * 12, 60)
  return {
    ...reminder,
    account_id: reminder?.account_id || accountId,
    auto_detection: {
      occurrences,
      latest_transaction_date: reminder?.auto_detection?.latest_transaction_date || '',
      confidence_score: Number.isFinite(serverConfidence) ? serverConfidence : fallbackConfidence,
    },
  }
}

/**
 * Sort reminders by due date first so nothing earlier is hidden by confidence.
 *
 * Ties: user-scheduled before auto-detected, then confidence, occurrences, and
 * finally description/account for a stable order.
 *
 * @param {Record<string, unknown>} left - Left reminder item.
 * @param {Record<string, unknown>} right - Right reminder item.
 * @returns {number} Comparator compatible with Array.sort.
 */
function compareReminders(left, right) {
  const dueDelta = String(left?.next_due_date || '').localeCompare(
    String(right?.next_due_date || ''),
  )
  if (dueDelta !== 0) return dueDelta

  const leftUser = left?.source === 'user' ? 0 : 1
  const rightUser = right?.source === 'user' ? 0 : 1
  if (leftUser !== rightUser) return leftUser - rightUser

  const confidenceDelta =
    (right?.auto_detection?.confidence_score || 0) - (left?.auto_detection?.confidence_score || 0)
  if (confidenceDelta !== 0) return confidenceDelta

  const occurrenceDelta =
    (right?.auto_detection?.occurrences || 0) - (left?.auto_detection?.occurrences || 0)
  if (occurrenceDelta !== 0) return occurrenceDelta

  const descriptionDelta = String(left?.description || '').localeCompare(
    String(right?.description || ''),
  )
  if (descriptionDelta !== 0) return descriptionDelta

  return String(left?.account_id || '').localeCompare(String(right?.account_id || ''))
}

/**
 * Describe when a reminder is due relative to today.
 *
 * @param {Record<string, unknown>} reminder - Normalized reminder.
 * @returns {string} "Today", "Tomorrow" or "In N days · Apr 11".
 */
function describeDue(reminder) {
  let days = Number(reminder?.days_until_due)
  if (!Number.isFinite(days)) {
    const due = parseISODate(reminder?.next_due_date)
    const today = parseISODate(formatAsISODate(new Date()))
    days = due && today ? Math.round((due - today) / 86400000) : NaN
  }
  if (days === 0) return 'Today'
  if (days === 1) return 'Tomorrow'
  const short = formatShortDate(reminder?.next_due_date)
  return Number.isFinite(days) ? `In ${days} days · ${short}` : `Due ${short}`
}

/**
 * Load recurring reminders for selected dashboard snapshot accounts.
 *
 * Failed accounts do not erase reminders from healthy ones; stale or superseded
 * responses are ignored.
 *
 * @param {{ force?: boolean }} [options] - Bypass the freshness TTL.
 * @returns {Promise<void>} Resolves once reminders are loaded (or gracefully degraded).
 */
async function loadUpcomingRecurringTransactions({ force = false } = {}) {
  const fresh =
    recurringStatus.value === 'ok' &&
    recurringFailedCount.value === 0 &&
    Date.now() - recurringFetchedAt < RECURRING_TTL_MS
  if (!force && fresh) {
    return
  }

  const requestId = ++recurringRequestId
  const isCurrent = () => !isUnmounted && requestId === recurringRequestId
  isLoadingRecurring.value = true

  try {
    const snapshotResponse = await api.getAccountSnapshot()
    if (!isCurrent()) return
    const selectedAccountIds = Array.isArray(snapshotResponse?.data?.selected_account_ids)
      ? snapshotResponse.data.selected_account_ids
      : []

    if (!selectedAccountIds.length) {
      upcomingReminders.value = []
      recurringAccountCount.value = 0
      recurringFailedCount.value = 0
      recurringStatus.value = 'no-accounts'
      recurringFetchedAt = Date.now()
      return
    }

    const results = await Promise.allSettled(
      selectedAccountIds.map(async (accountId) => {
        const response = await getRecurringTransactions(accountId)
        if (response?.status !== 'success') {
          throw new Error('Recurring request did not succeed')
        }
        const rawReminders = Array.isArray(response?.reminders) ? response.reminders : []
        return rawReminders.map((reminder) => normalizeReminder(reminder, accountId))
      }),
    )
    if (!isCurrent()) return

    const failed = results.filter((result) => result.status === 'rejected').length
    recurringAccountCount.value = selectedAccountIds.length
    recurringFailedCount.value = failed
    if (failed === results.length) {
      upcomingReminders.value = []
      recurringStatus.value = 'error'
      return
    }
    upcomingReminders.value = results
      .filter((result) => result.status === 'fulfilled')
      .flatMap((result) => result.value)
      .sort(compareReminders)
    recurringStatus.value = 'ok'
    recurringFetchedAt = Date.now()
  } catch (error) {
    if (!isCurrent()) return
    upcomingReminders.value = []
    recurringFailedCount.value = 0
    recurringStatus.value = 'error'
  } finally {
    if (isCurrent()) {
      isLoadingRecurring.value = false
    }
  }
}

function retryRecurring() {
  loadUpcomingRecurringTransactions({ force: true })
}

watch(isExtendedView, (showExtended) => {
  if (showExtended) {
    loadUpcomingRecurringTransactions()
  }
})

onMounted(() => {
  if (isExtendedView.value) {
    loadUpcomingRecurringTransactions()
  }
})

onBeforeUnmount(() => {
  isUnmounted = true
})

// ---------------------------------------------------------------------------
// Period statistics
// ---------------------------------------------------------------------------

/**
 * Build an inclusive list of date labels between two ISO date strings.
 *
 * @param {string} startISO - Inclusive start date (YYYY-MM-DD).
 * @param {string} endISO - Inclusive end date (YYYY-MM-DD).
 * @returns {string[]} Ordered list of ISO date labels.
 */
function buildDateRangeLabels(startISO, endISO) {
  const start = parseISODate(startISO)
  const end = parseISODate(endISO)
  if (!start || !end) return []

  const labels = []
  const cursor = new Date(Math.min(start, end))
  const last = new Date(Math.max(start, end))
  while (cursor <= last) {
    labels.push(formatAsISODate(cursor))
    cursor.setDate(cursor.getDate() + 1)
  }
  return labels
}

/**
 * Create a zero-filled chart entry for the supplied date label.
 *
 * @param {string} date - ISO date string.
 * @returns {Object} Zero-valued chart entry.
 */
function createZeroFilledEntry(date) {
  return {
    date,
    income: { parsedValue: 0 },
    expenses: { parsedValue: 0 },
    net: { parsedValue: 0 },
    transaction_count: 0,
  }
}

const paddedChartData = computed(() => {
  const data = Array.isArray(props.chartData) ? props.chartData : []
  const parsedStart = parseISODate(props.startDate)
  const parsedDetail = parseISODate(detailDate.value)
  const parsedEnd = parseISODate(props.endDate)

  const sortedDates = data
    .map((d) => parseISODate(d?.date))
    .filter(Boolean)
    .sort((a, b) => a - b)

  const start = parsedStart || sortedDates[0]
  const end = parsedDetail || parsedEnd || sortedDates.at(-1)
  if (!start || !end) {
    return data
  }

  const labels = buildDateRangeLabels(formatAsISODate(start), formatAsISODate(end))
  if (!labels.length) {
    return data
  }

  const byDate = new Map(data.map((entry) => [entry?.date, entry]))
  return labels.map((label) => byDate.get(label) ?? createZeroFilledEntry(label))
})

const filteredChartData = computed(() => {
  const data = paddedChartData.value
  const cutoff = parseISODate(detailDate.value)
  if (!cutoff) {
    return data
  }

  return data.filter((entry) => {
    const entryDate = parseISODate(entry?.date)
    if (!entryDate) {
      return false
    }
    return entryDate <= cutoff
  })
})

const detailSummary = computed(() => {
  const data = filteredChartData.value
  if (!data.length) {
    const hasRawData = Array.isArray(props.chartData) && props.chartData.length > 0
    if (!hasRawData) {
      return {
        totalIncome: props.summary?.totalIncome ?? 0,
        totalExpenses: props.summary?.totalExpenses ?? 0,
        totalNet: props.summary?.totalNet ?? 0,
      }
    }
    return { totalIncome: 0, totalExpenses: 0, totalNet: 0 }
  }

  const totals = data.reduce(
    (acc, entry) => {
      acc.totalIncome += entry?.income?.parsedValue || 0
      acc.totalExpenses += entry?.expenses?.parsedValue || 0
      acc.totalNet += entry?.net?.parsedValue || 0
      return acc
    },
    { totalIncome: 0, totalExpenses: 0, totalNet: 0 },
  )

  return totals
})

const viewingDateLabel = computed(() => {
  const cutoff = parseISODate(detailDate.value)
  if (!cutoff) {
    return 'today'
  }
  return cutoff.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  })
})

const netPolarityClass = computed(() => ({
  positive: detailSummary.value.totalNet >= 0,
  negative: detailSummary.value.totalNet < 0,
}))

/** Net as a percent of income; null when there is no income to divide by. */
const netPercentOfIncomeLabel = computed(() => {
  const income = detailSummary.value.totalIncome
  if (!(income > 0)) return ''
  const pct = Math.round((detailSummary.value.totalNet / income) * 1000) / 10
  return `${pct}%`
})

const dayCountLabel = computed(() => {
  const n = filteredChartData.value.length
  return `${n} ${n === 1 ? 'day' : 'days'}`
})

// Extended statistics calculations
const extendedMetrics = computed(() => {
  const data = filteredChartData.value
  if (!data.length) {
    return {
      avgDailyIncome: 0,
      avgDailyExpenses: 0,
      avgDailyNet: 0,
      netMA7: null,
      netMA30: null,
      netChange: 0,
      incomeChange: 0,
      expenseChange: 0,
      volatility: 0,
      topEarningDay: null,
      topSpendingDay: null,
      outlierDays: [],
    }
  }

  const days = data.length

  // Daily aggregates (zero-activity days included)
  const incomeValues = data.map((d) => d.income?.parsedValue || 0)
  const expenseValues = data.map((d) => Math.abs(d.expenses?.parsedValue || 0))
  const netValues = data.map((d) => d.net?.parsedValue || 0)

  const avgDailyIncome = detailSummary.value.totalIncome / days
  const avgDailyExpenses = detailSummary.value.totalExpenses / days
  const avgDailyNet = detailSummary.value.totalNet / days

  const netMA7 = calculateMovingAverage(netValues, 7)
  const netMA30 = calculateMovingAverage(netValues, 30)

  const netChange = netValues[netValues.length - 1] - netValues[0]
  const incomeChange = incomeValues[incomeValues.length - 1] - incomeValues[0]
  const expenseChange = expenseValues[expenseValues.length - 1] - expenseValues[0]
  const volatility = calculateVolatility(netValues)

  // Highest income/expense days
  const maxIncomeIdx = incomeValues.indexOf(Math.max(...incomeValues))
  const maxExpenseIdx = expenseValues.indexOf(Math.max(...expenseValues))
  const topEarningDay = data[maxIncomeIdx]
    ? { date: data[maxIncomeIdx].date, amount: incomeValues[maxIncomeIdx] }
    : null
  const topSpendingDay = data[maxExpenseIdx]
    ? { date: data[maxExpenseIdx].date, amount: expenseValues[maxExpenseIdx] }
    : null

  // Days whose net is more than 2 standard deviations from the mean, largest first.
  // Needs a minimum sample and non-zero spread to say anything meaningful.
  let outlierDays = []
  if (days >= MIN_OUTLIER_SAMPLE_DAYS && volatility > 0) {
    const mean = netValues.reduce((a, b) => a + b, 0) / days
    const threshold = 2 * volatility
    outlierDays = data
      .map((d, i) => ({ date: d.date, deviation: Math.abs(netValues[i] - mean) }))
      .filter((d) => d.deviation > threshold)
      .sort((a, b) => b.deviation - a.deviation || a.date.localeCompare(b.date))
      .map((d) => d.date)
  }

  return {
    avgDailyIncome,
    avgDailyExpenses,
    avgDailyNet,
    netMA7,
    netMA30,
    netChange,
    incomeChange,
    expenseChange,
    volatility,
    topEarningDay,
    topSpendingDay,
    outlierDays,
  }
})

const unusualDays = computed(() => extendedMetrics.value.outlierDays.slice(0, MAX_UNUSUAL_DAYS))
const unusualDaysEmptyLabel = computed(() =>
  filteredChartData.value.length < MIN_OUTLIER_SAMPLE_DAYS ? 'Not enough history' : 'None found',
)

const topEarningAmountValue = computed(() => extendedMetrics.value.topEarningDay?.amount ?? null)
const topSpendingAmountValue = computed(() => {
  const amount = extendedMetrics.value.topSpendingDay?.amount
  return amount == null ? null : -Math.abs(amount)
})

const topEarningDateLabel = computed(() => extendedMetrics.value.topEarningDay?.date ?? 'N/A')
const topSpendingDateLabel = computed(() => extendedMetrics.value.topSpendingDay?.date ?? 'N/A')

const topEarningAmountLabel = computed(() => {
  if (topEarningAmountValue.value === null) return ''
  return formatAmount(topEarningAmountValue.value)
})

const topSpendingAmountLabel = computed(() => {
  if (topSpendingAmountValue.value === null) return ''
  return formatAmount(topSpendingAmountValue.value)
})

/**
 * Average of the trailing `period` values, or null until a full window exists.
 *
 * @param {number[]} values - Daily values, oldest first.
 * @param {number} period - Window length in days.
 * @returns {number | null} Window average or null with insufficient history.
 */
function calculateMovingAverage(values, period) {
  if (values.length < period) return null
  const recent = values.slice(-period)
  return recent.reduce((a, b) => a + b, 0) / period
}

/**
 * Format a moving average, explaining when the window is not yet full.
 *
 * @param {number | null} value - Moving average.
 * @param {number} period - Window length in days.
 * @returns {string} Display label.
 */
function movingAverageLabel(value, period) {
  return value === null ? `N/A (needs ${period} days)` : formatAmount(value)
}

function calculateVolatility(values) {
  const n = values.length
  if (n < 2) return 0

  const mean = values.reduce((a, b) => a + b, 0) / n
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n
  return Math.sqrt(variance)
}

const positiveDaysLabel = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0)
  const n = values.length
  if (!n) return 'N/A'
  const pos = values.filter((v) => v > 0).length
  const pct = Math.round((pos / n) * 1000) / 10
  return `${pct}% (${pos}/${n})`
})

const negativeDaysLabel = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0)
  const n = values.length
  if (!n) return 'N/A'
  const neg = values.filter((v) => v < 0).length
  const pct = Math.round((neg / n) * 1000) / 10
  return `${pct}% (${neg}/${n})`
})

const avgPositiveNetDayValue = computed(() => {
  const values = filteredChartData.value.map((d) => d.net?.parsedValue || 0).filter((v) => v > 0)
  if (!values.length) return null
  return values.reduce((a, b) => a + b, 0) / values.length
})

const avgPositiveNetDayLabel = computed(() => {
  if (avgPositiveNetDayValue.value === null) return 'N/A'
  return formatAmount(avgPositiveNetDayValue.value)
})

/**
 * Convert a date string into a Date instance using local timezone.
 *
 * @param {string | Date | undefined | null} input - ISO-like date string or Date.
 * @returns {Date | null} Parsed Date instance, or null if invalid.
 */
function parseISODate(input) {
  if (input instanceof Date) {
    return Number.isNaN(input.getTime()) ? null : input
  }
  if (!input) {
    return null
  }
  const normalized = typeof input === 'string' ? `${input}T00:00:00` : input
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/**
 * Format a Date instance as YYYY-MM-DD.
 *
 * @param {Date} date - Date to format.
 * @returns {string} ISO formatted date string.
 */
function formatAsISODate(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) {
    return ''
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Clamp a date string so it falls within the specified range.
 *
 * @param {string} value - The target date string.
 * @param {string} min - Lower bound date string.
 * @param {string} max - Upper bound date string.
 * @returns {string} A valid date string within the supplied bounds.
 */
function clampDateString(value, min, max) {
  const parsedValue = parseISODate(value)
  const parsedMin = parseISODate(min)
  const parsedMax = parseISODate(max)

  let result = parsedValue || parsedMax || parseISODate(TODAY_ISO) || new Date()

  if (parsedMin && result < parsedMin) {
    result = parsedMin
  }
  if (parsedMax && result > parsedMax) {
    result = parsedMax
  }

  return formatAsISODate(result)
}
</script>

<style scoped>
.statistics-container {
  background: var(--color-bg-sec);
  border: 1px solid var(--divider);
  border-radius: 12px;
  padding: 1rem;
  margin-top: 1rem;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
}

.stats-period {
  margin: 0.15rem 0 0;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.accent-toggle-btn:focus-visible,
.detail-date-reset:focus-visible,
.recurring-upcoming-retry:focus-visible,
.unusual-day-btn:focus-visible,
.more-statistics summary:focus-visible,
.recurring-upcoming-link:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.stats-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.period-summary {
  margin-top: 1rem;
}

.period-summary-grid .stat-item {
  flex-wrap: wrap;
  min-width: 0;
}

.period-summary-grid .stat-value {
  overflow-wrap: anywhere;
}

.period-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem 1.5rem;
}

.more-statistics {
  margin-top: 1rem;
}

.more-statistics summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
}

.more-statistics-note {
  margin: 0.5rem 0;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.unusual-days {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  justify-content: flex-end;
}

.unusual-day-btn {
  padding: 0.1rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid var(--divider);
  background: transparent;
  color: var(--color-accent-cyan);
  font-size: 0.78rem;
  cursor: pointer;
}

.recurring-upcoming-warning {
  margin: 0 0 0.5rem;
  font-size: 0.8rem;
  color: var(--color-accent-yellow);
}

.recurring-upcoming-retry {
  margin-left: 0.5rem;
  padding: 0.1rem 0.6rem;
  border-radius: 9999px;
  border: 1px solid var(--divider);
  background: transparent;
  color: var(--color-accent-cyan);
  font-size: 0.75rem;
  cursor: pointer;
}

.recurring-upcoming-more {
  margin: 0.5rem 0 0;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.recurring-upcoming-link {
  display: inline-block;
  margin-top: 0.6rem;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-decoration: underline;
}

.recurring-upcoming-message {
  margin: 0 0 0.35rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.stat-label {
  font-weight: 600;
  font-size: 0.9rem;
}

.stat-value {
  font-weight: 700;
  font-size: 0.95rem;
}

.stat-income .stat-label {
  color: var(--color-accent-cyan);
}

.stat-expenses .stat-label {
  color: var(--color-accent-red);
}

.stat-net.positive .stat-label,
.stat-net.positive .stat-value {
  color: var(--color-accent-green);
}

.stat-net.negative .stat-label,
.stat-net.negative .stat-value {
  color: var(--color-accent-red);
}

.extended-stats {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--divider);
}

.detail-date-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.detail-date-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-text-muted);
}

.detail-date-input {
  min-width: 0;
  max-width: 100%;
  padding: 0.35rem 0.75rem;
  border-radius: 6px;
  border: 1px solid var(--divider);
  background: var(--color-bg-sec);
  color: var(--color-text-light);
}

.detail-date-input:focus {
  outline: none;
  border-color: var(--color-accent-cyan);
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
}

.detail-date-reset {
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  border: 1px solid var(--color-accent-cyan);
  background: transparent;
  color: var(--color-accent-cyan);
  font-size: 0.75rem;
  font-weight: 600;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.detail-date-reset:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(0, 217, 255, 0.25);
}

.detail-date-helper {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.recurring-upcoming-panel {
  border: 1px solid color-mix(in srgb, var(--color-accent-cyan) 25%, transparent);
  border-radius: 0.75rem;
  padding: 0.9rem 1rem;
  background: color-mix(in srgb, var(--color-bg-sec) 88%, black 12%);
  margin-top: 0.75rem;
}

.recurring-upcoming-header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.4rem 0.75rem;
  margin-bottom: 0.55rem;
}

.recurring-upcoming-subtitle {
  margin: 0;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.recurring-upcoming-state {
  margin: 0;
  font-size: 0.84rem;
  color: var(--color-text-muted);
}

.recurring-upcoming-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.5rem;
}

.recurring-upcoming-item {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.55rem 0.7rem;
  border-radius: 0.6rem;
  background: color-mix(in srgb, var(--color-accent-cyan) 9%, transparent);
}

.recurring-upcoming-description {
  font-size: 0.9rem;
  font-weight: 600;
}

.recurring-upcoming-meta {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.recurring-upcoming-amount {
  align-self: center;
  font-size: 0.86rem;
  font-weight: 700;
}

.stats-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 1rem;
}

.stat-group {
  min-width: 0;
}

@media (min-width: 769px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.stat-group {
  padding: 0.25rem 0;
}

.group-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-accent-yellow);
  margin: 0 0 0.5rem 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.group-subtitle-inline {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: none;
  margin-left: 0.5rem;
}

.stat-group .stat-item {
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
  flex-wrap: wrap;
  min-width: 0;
  justify-content: space-between;
}

.subsection-title {
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-top: 1px dashed var(--divider);
  padding-top: 0.25rem;
}

.stat-group .stat-label {
  color: var(--color-text-muted);
}

.stat-group .stat-value {
  color: var(--color-text-light);
}

.stat-value.amount-positive {
  color: var(--text-positive);
}

.stat-value.amount-negative {
  color: var(--text-negative);
}

.outlier-value {
  display: inline-flex;
  align-items: baseline;
  gap: 0.35rem;
}

.outlier-amount {
  font-variant-numeric: tabular-nums;
}

.badge-note {
  display: inline-block;
  margin-left: 0.25rem;
  padding: 0 0.35rem;
  font-size: 0.7rem;
  line-height: 1.2;
  color: var(--color-text-muted);
  border: 1px solid var(--divider);
  border-radius: 4px;
  text-transform: lowercase;
}

.trend-indicator {
  font-weight: 700;
}

.trend-up {
  color: var(--color-accent-green);
}

.trend-down {
  color: var(--color-accent-red);
}

.trend-flat {
  color: var(--color-accent-yellow);
}

/* Transition: opacity only, no fixed-height clipping */
.expand-enter-active,
.expand-leave-active {
  transition: opacity 0.2s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .expand-enter-active,
  .expand-leave-active,
  .detail-date-reset {
    transition: none;
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .period-summary-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stats-header {
    flex-wrap: wrap;
  }
}
</style>
