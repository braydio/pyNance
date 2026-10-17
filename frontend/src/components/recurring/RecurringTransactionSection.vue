<!--
  RecurringTransactionSection.vue
  -------------------------------
  Review and manage recurring cash plans across all accounts (or one).

  Sections: "Needs review" (detected suggestions you confirm or dismiss), "Confirmed & upcoming",
  and a collapsed "Ignored & ended". Suggestions are never treated as bills until confirmed. Manual
  plans only need an account, a name, an amount and a date; no existing transaction is required.
-->

<template>
  <section id="recurring" class="recurring-manager" aria-labelledby="recurring-heading">
    <div class="recurring-header">
      <div>
        <h2 id="recurring-heading" class="heading-md">Recurring Transactions</h2>
        <p class="text-muted">
          Bills and income that repeat. Suggestions below are only used for your forecast after you
          confirm them.
        </p>
      </div>
      <div class="recurring-actions">
        <label class="visually-hidden" for="recurring-account">Account</label>
        <select
          id="recurring-account"
          v-model="selectedAccount"
          class="input select"
          data-testid="recurring-account"
          @change="load"
        >
          <option value="">All accounts</option>
          <option v-for="acct in accountOptions" :key="acct.account_id" :value="acct.account_id">
            {{ acct.name }}
          </option>
        </select>
        <button type="button" class="btn btn-outline" @click="startNew">+ Add plan</button>
        <button
          type="button"
          class="btn btn-outline"
          :disabled="scanning"
          data-testid="scan-button"
          @click="scan"
        >
          {{ scanning ? 'Scanning...' : 'Scan for recurring' }}
        </button>
      </div>
    </div>

    <p v-if="scanSummary" class="text-muted" role="status" data-testid="scan-summary">
      {{ scanSummary }}
    </p>
    <p v-if="error" class="text-negative" role="alert" data-testid="recurring-error">
      {{ error }}
      <button type="button" class="btn-sm" @click="load">Retry</button>
    </p>
    <p v-if="loading" class="text-muted" role="status">Loading recurring plans...</p>

    <!-- Add / edit form -->
    <form
      v-if="showForm"
      class="recurring-form"
      aria-label="Recurring plan"
      data-testid="recurring-form"
      @submit.prevent="save"
    >
      <label>
        <span>Account</span>
        <select v-model="form.account_id" class="input select" required aria-label="Plan account">
          <option value="" disabled>Choose an account</option>
          <option v-for="acct in accountOptions" :key="acct.account_id" :value="acct.account_id">
            {{ acct.name }}
          </option>
        </select>
      </label>
      <label>
        <span>Name</span>
        <input
          v-model="form.display_name"
          class="input"
          required
          maxlength="256"
          placeholder="e.g. Duke Energy"
          aria-label="Plan name"
        />
      </label>
      <label>
        <span>Amount ($)</span>
        <input
          v-model="form.amount"
          class="input"
          type="number"
          min="0"
          step="0.01"
          required
          aria-label="Plan amount in dollars"
        />
      </label>
      <label>
        <span>Direction</span>
        <select v-model="form.direction" class="input select" aria-label="Money direction">
          <option value="out">Money out (bill)</option>
          <option value="in">Money in (income)</option>
        </select>
      </label>
      <label>
        <span>Repeats</span>
        <select v-model="form.cadence" class="input select" aria-label="Repeats">
          <option v-for="option in cadenceOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <label>
        <span>Amount type</span>
        <select v-model="form.amount_mode" class="input select" aria-label="Amount type">
          <option value="fixed">Same every time</option>
          <option value="variable">Varies (estimate)</option>
        </select>
      </label>
      <label>
        <span>Next due date</span>
        <input
          v-model="form.anchor_date"
          class="input"
          type="date"
          required
          aria-label="Next due date"
        />
      </label>
      <label>
        <span>Notes</span>
        <input v-model="form.notes" class="input" aria-label="Notes" placeholder="Optional" />
      </label>
      <p v-if="formError" class="text-negative form-error" role="alert">{{ formError }}</p>
      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : form.id ? 'Save changes' : 'Add plan' }}
        </button>
        <button type="button" class="btn btn-outline" @click="cancelForm">Cancel</button>
      </div>
    </form>

    <!-- Needs review -->
    <div class="plan-section" aria-labelledby="needs-review-heading" data-testid="needs-review">
      <h3 id="needs-review-heading" class="subheading">Needs review ({{ candidates.length }})</h3>
      <p v-if="!loading && !candidates.length" class="text-muted">
        Nothing to review. Run a scan to look for repeating payments in your history.
      </p>
      <ul v-else class="plan-list">
        <li
          v-for="item in candidates"
          :key="item.stream_id"
          class="plan-card"
          :data-testid="`candidate-${item.stream_id}`"
        >
          <div class="plan-main">
            <p class="plan-title">{{ item.display_name }}</p>
            <p class="plan-meta">
              {{ amountText(item) }} · {{ cadenceLabel(item.cadence) }} · next
              {{ item.next_due_date || 'unknown' }} · {{ accountName(item.account_id) }}
            </p>
            <p class="text-muted">{{ item.explanation }}</p>
            <ul v-if="item.evidence?.length" class="evidence" aria-label="Recent matching payments">
              <li v-for="row in item.evidence" :key="row.date + row.amount">
                {{ row.date }} · {{ formatAmount(row.amount) }}
              </li>
            </ul>
          </div>
          <div class="plan-actions">
            <button
              type="button"
              class="btn btn-primary"
              :disabled="busy[item.stream_id]"
              :aria-label="`Confirm ${item.display_name} as recurring`"
              @click="decide(item, 'confirmed')"
            >
              Confirm
            </button>
            <button
              type="button"
              class="btn btn-outline"
              :disabled="busy[item.stream_id]"
              :aria-label="`Edit ${item.display_name}`"
              @click="startEdit(item)"
            >
              Edit
            </button>
            <button
              type="button"
              class="btn btn-outline"
              :disabled="busy[item.stream_id]"
              :aria-label="`${item.display_name} is not recurring`"
              @click="decide(item, 'ignored')"
            >
              Not recurring
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Confirmed & upcoming -->
    <div class="plan-section" aria-labelledby="confirmed-heading" data-testid="confirmed">
      <h3 id="confirmed-heading" class="subheading">
        Confirmed &amp; upcoming ({{ confirmed.length }})
      </h3>
      <p v-if="!loading && !confirmed.length" class="text-muted">
        No confirmed plans yet. Add one, or confirm a suggestion above.
      </p>
      <ul v-else class="plan-list">
        <li v-for="item in confirmed" :key="item.stream_id" class="plan-card">
          <div class="plan-main">
            <p class="plan-title">{{ item.display_name }}</p>
            <p class="plan-meta">
              <span :class="amountPolarityClass(item.amount_cash_delta)">{{
                amountText(item)
              }}</span>
              · {{ cadenceLabel(item.cadence) }} · next {{ item.next_due_date || 'none' }} ·
              {{ accountName(item.account_id) }}
            </p>
            <p v-if="item.notes" class="text-muted">{{ item.notes }}</p>
          </div>
          <div class="plan-actions">
            <button
              type="button"
              class="btn btn-outline"
              :aria-label="`Edit ${item.display_name}`"
              @click="startEdit(item)"
            >
              Edit
            </button>
            <button
              type="button"
              class="btn btn-outline"
              :disabled="busy[item.stream_id]"
              :aria-label="`End ${item.display_name}`"
              @click="decide(item, 'ended')"
            >
              End
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Ignored & ended (collapsed) -->
    <details class="plan-section" data-testid="inactive">
      <summary class="subheading">Ignored &amp; ended ({{ inactive.length }})</summary>
      <p v-if="!inactive.length" class="text-muted">Nothing here.</p>
      <ul v-else class="plan-list">
        <li v-for="item in inactive" :key="item.stream_id" class="plan-card">
          <div class="plan-main">
            <p class="plan-title">{{ item.display_name }}</p>
            <p class="plan-meta">
              {{ item.status === 'ignored' ? 'Not recurring' : 'Ended' }} · {{ amountText(item) }} ·
              {{ cadenceLabel(item.cadence) }}
            </p>
          </div>
          <div class="plan-actions">
            <button
              type="button"
              class="btn btn-outline"
              :disabled="busy[item.stream_id]"
              :aria-label="`Confirm ${item.display_name} as recurring`"
              @click="decide(item, 'confirmed')"
            >
              Confirm
            </button>
          </div>
        </li>
      </ul>
    </details>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '@/services/api'
import {
  createRecurringStream,
  decideRecurringStream,
  getRecurringCandidates,
  getRecurringStreams,
  scanRecurring,
  updateRecurringStream,
} from '@/api/recurring'
import { amountPolarityClass, formatAmount } from '@/utils/format'

const props = defineProps({
  /** Optional: limit to one account. Empty means all accounts. */
  accountId: { type: String, default: '' },
  /** Optional: already-known accounts ({ account_id, name }) to avoid refetching. */
  accounts: { type: Array, default: null },
})

const cadenceOptions = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Every 2 weeks' },
  { value: 'semimonthly', label: 'Twice a month' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'once', label: 'One time' },
]

const accountList = ref([])
const selectedAccount = ref(props.accountId || '')
const loading = ref(true)
const scanning = ref(false)
const saving = ref(false)
const error = ref('')
const formError = ref('')
const scanSummary = ref('')
const showForm = ref(false)
const streams = ref([])
const candidates = ref([])
const busy = reactive({})

const blankForm = () => ({
  id: '',
  account_id: selectedAccount.value || '',
  display_name: '',
  amount: '',
  direction: 'out',
  cadence: 'monthly',
  amount_mode: 'fixed',
  anchor_date: '',
  notes: '',
})
const form = reactive(blankForm())

const accountOptions = computed(() => props.accounts ?? accountList.value)
const confirmed = computed(() =>
  streams.value
    .filter((s) => s.status === 'confirmed')
    .sort((a, b) => (a.next_due_date || '9999').localeCompare(b.next_due_date || '9999')),
)
const inactive = computed(() =>
  streams.value.filter((s) => ['ignored', 'ended'].includes(s.status)),
)

function cadenceLabel(value) {
  return cadenceOptions.find((o) => o.value === value)?.label ?? value
}

function accountName(accountId) {
  return accountOptions.value.find((a) => a.account_id === accountId)?.name ?? 'Account'
}

/** "$83.00 - $97.00" for variable amounts, a single amount otherwise. */
function amountText(item) {
  const low = Number(item.amount_range?.min ?? item.amount_cash_delta)
  const high = Number(item.amount_range?.max ?? item.amount_cash_delta)
  if (low !== high) return `${formatAmount(low)} to ${formatAmount(high)}`
  return formatAmount(item.amount_cash_delta)
}

function describeError(err, fallback) {
  const data = err?.response?.data
  if (data?.code === 'owner_not_configured') {
    return 'Recurring plans are not set up on this server yet (PYNANCE_OWNER_USER_ID is missing).'
  }
  return data?.message || fallback
}

async function load() {
  loading.value = true
  error.value = ''
  const account_id = selectedAccount.value || undefined
  try {
    const [all, review] = await Promise.all([
      getRecurringStreams({ account_id, page_size: 100 }),
      getRecurringCandidates({ account_id }),
    ])
    candidates.value = review.candidates || []
    const reviewIds = new Set(candidates.value.map((c) => c.stream_id))
    streams.value = (all.streams || []).filter((s) => !reviewIds.has(s.stream_id))
  } catch (err) {
    console.error('Failed to load recurring plans:', err)
    error.value = describeError(err, 'Unable to load recurring plans.')
  } finally {
    loading.value = false
  }
}

async function scan() {
  scanning.value = true
  error.value = ''
  scanSummary.value = ''
  try {
    const res = await scanRecurring({
      account_ids: selectedAccount.value ? [selectedAccount.value] : undefined,
      dry_run: false,
    })
    const s = res.summary || {}
    scanSummary.value =
      `Scan finished: ${s.created || 0} new ${s.created === 1 ? 'suggestion' : 'suggestions'}` +
      (s.history_incomplete ? '. Only part of the history I look for was available.' : '.')
    await load()
  } catch (err) {
    console.error('Failed to scan recurring transactions:', err)
    error.value = describeError(err, 'Unable to scan for recurring payments.')
  } finally {
    scanning.value = false
  }
}

async function decide(item, decision) {
  busy[item.stream_id] = true
  error.value = ''
  try {
    await decideRecurringStream(item.stream_id, decision)
    await load()
  } catch (err) {
    console.error('Failed to record decision:', err)
    error.value = describeError(err, 'Could not save your choice. Nothing was changed.')
  } finally {
    busy[item.stream_id] = false
  }
}

function resetForm(values = {}) {
  Object.assign(form, blankForm(), values)
  formError.value = ''
}

function startNew() {
  resetForm()
  showForm.value = true
}

function startEdit(item) {
  const delta = Number(item.amount_cash_delta)
  resetForm({
    id: item.stream_id,
    account_id: item.account_id,
    display_name: item.display_name,
    amount: Math.abs(delta).toFixed(2),
    direction: delta >= 0 ? 'in' : 'out',
    cadence: item.cadence,
    amount_mode: item.amount_mode || 'fixed',
    anchor_date: item.next_due_date || '',
    notes: item.notes || '',
  })
  showForm.value = true
}

/**
 * Open the form pre-filled from a transaction row. Called by the parent through the exposed API; the
 * transaction id is never shown or required, only its name, amount and account are reused.
 *
 * @param {{description?: string, merchant_name?: string, amount?: number|string,
 *   account_id?: string, provider?: string, date?: string}} tx
 */
function openFromTransaction(tx = {}) {
  const raw = Number(tx.amount_cash_delta ?? tx.amount ?? 0)
  // Stored Plaid amounts are + money out; an explicit cash delta is + money in.
  const outflow =
    tx.amount_cash_delta !== undefined ? raw < 0 : tx.provider === 'plaid' ? raw >= 0 : true
  resetForm({
    account_id: tx.account_id || selectedAccount.value || '',
    display_name:
      tx.merchant_name && tx.merchant_name !== 'Unknown' ? tx.merchant_name : tx.description || '',
    amount: Math.abs(raw).toFixed(2),
    direction: outflow ? 'out' : 'in',
    anchor_date: '',
    notes: tx.notes || '',
  })
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  resetForm()
}

async function save() {
  formError.value = ''
  const amount = Number(form.amount)
  if (!form.account_id) return (formError.value = 'Choose an account.')
  if (!form.display_name.trim()) return (formError.value = 'Enter a name.')
  if (!Number.isFinite(amount) || amount <= 0)
    return (formError.value = 'Enter an amount above zero.')
  if (!form.anchor_date) return (formError.value = 'Choose the next due date.')

  const payload = {
    account_id: form.account_id,
    display_name: form.display_name.trim(),
    amount_cash_delta: (form.direction === 'in' ? amount : -amount).toFixed(2),
    amount_mode: form.amount_mode,
    cadence: form.cadence,
    anchor_date: form.anchor_date,
    notes: form.notes || null,
  }
  saving.value = true
  try {
    if (form.id) await updateRecurringStream(form.id, payload)
    else await createRecurringStream(payload)
    showForm.value = false
    resetForm()
    await load()
  } catch (err) {
    console.error('Error saving recurring plan:', err)
    formError.value = describeError(err, 'Could not save this plan. Nothing was changed.')
  } finally {
    saving.value = false
  }
}

defineExpose({ openFromTransaction, reload: load })

onMounted(async () => {
  if (props.accounts === null) {
    try {
      const data = await api.getAccounts()
      accountList.value = data.accounts || []
    } catch (err) {
      console.error('Failed to load accounts for recurring plans:', err)
    }
  }
  await load()
})
</script>

<style scoped>
@reference "../../assets/css/main.css";

.recurring-manager {
  width: 100%;
  margin-top: 2rem;
  padding: 2rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.recurring-header {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: space-between;
  align-items: flex-start;
}

.recurring-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.heading-md {
  font-size: 1.6rem;
  font-weight: bold;
  color: var(--text-warning);
  margin-bottom: 0.25rem;
}

.subheading {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--color-text-muted);
  margin: 1.5rem 0 0.75rem;
}

.recurring-form {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1.25rem;
}

.recurring-form label {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.form-error,
.form-actions {
  grid-column: 1 / -1;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.plan-list {
  display: grid;
  gap: 0.75rem;
  list-style: none;
  padding: 0;
  margin: 0;
}

.plan-card {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  justify-content: space-between;
  padding: 1rem;
  background-color: var(--color-bg-dark);
  border: 1px solid var(--divider);
  border-radius: 8px;
}

.plan-main {
  min-width: 0;
  flex: 1 1 18rem;
}

.plan-title {
  font-weight: 600;
}

.plan-meta {
  font-size: 0.9rem;
}

.evidence {
  margin: 0.5rem 0 0;
  padding-left: 1.25rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.plan-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: flex-start;
}

.btn-sm {
  background: transparent;
  border: none;
  cursor: pointer;
  min-height: var(--control-height-sm);
  padding: 0 0.5rem;
  font-size: 0.875rem;
  color: var(--text-link);
}

.btn-sm:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

@media (max-width: 640px) {
  .recurring-manager {
    padding: 1rem;
  }
}
</style>
