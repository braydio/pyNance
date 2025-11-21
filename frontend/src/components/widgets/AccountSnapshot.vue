<!--
  AccountSnapshot.vue
  Enhanced dashboard snapshot with persisted selections, staged edits, and richer drilldowns.
  Editing is opt-in: click Edit, adjust the staged selection (up to maxSelection), then Save to
  persist or Cancel to revert to the last saved snapshot.
-->
<template>
  <div class="bg-bg-secondary rounded-3xl p-6 shadow-card w-full max-w-3xl">
    <header class="flex flex-wrap items-start justify-between gap-4">
      <div class="space-y-1">
        <h3 class="text-lg font-semibold text-blue-950 dark:text-blue-100">Account Snapshot</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">
          Persisted to your dashboard. Choose up to {{ maxSelection }} accounts to stay in sync.
        </p>
        <p v-if="errorMessage" class="text-xs text-red-500">{{ errorMessage }}</p>
        <p
          v-else-if="metadata.discarded_ids?.length"
          class="text-xs text-amber-600 dark:text-amber-400"
        >
          Removed {{ metadata.discarded_ids.length }} saved account
          {{ metadata.discarded_ids.length === 1 ? '' : 's' }} that are no longer available.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2 text-xs">
        <button
          type="button"
          class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-3 py-1.5 font-medium text-gray-600 transition hover:border-primary hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:focus-visible:ring-offset-gray-900"
          aria-label="Refresh account snapshot"
          @click="handleRefresh"
          :disabled="isLoading || isSaving"
          aria-label="Refresh account snapshot"
        >
          <span class="i-carbon-renew text-sm" aria-hidden="true"></span>
          <span>{{ isLoading ? 'Refreshing…' : 'Refresh' }}</span>
        </button>
        <button
          v-if="!isEditing"
          type="button"
          class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-3 py-1.5 font-medium text-gray-600 transition hover:border-primary hover:text-primary focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:focus-visible:ring-offset-gray-900"
          @click="startEditing"
          :disabled="isLoading || isSaving"
          aria-label="Edit snapshot selection"
        >
          <span class="i-carbon-edit text-sm" aria-hidden="true"></span>
          <span>Edit</span>
        </button>
        <button
          v-else
          type="button"
          class="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 font-medium text-emerald-700 transition hover:border-emerald-400 hover:text-emerald-800 focus-visible:ring-2 focus-visible:ring-emerald-400/60 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 dark:border-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-200 dark:focus-visible:ring-offset-gray-900"
          @click="saveEditing"
          :disabled="isSaving || !hasStagedChanges"
          :aria-label="isSaving ? 'Saving snapshot' : 'Save snapshot selection'"
        >
          <span class="i-carbon-save text-sm" aria-hidden="true"></span>
          <span>{{ isSaving ? 'Saving…' : 'Save' }}</span>
        </button>
        <button
          v-if="isEditing"
          type="button"
          class="inline-flex items-center gap-1 rounded-full border border-gray-200 bg-white px-3 py-1.5 font-medium text-gray-600 transition hover:border-primary hover:text-primary focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:focus-visible:ring-offset-gray-900"
          @click="cancelEditing"
          :disabled="isSaving"
          aria-label="Cancel snapshot edits"
        >
          <span class="i-carbon-close text-sm" aria-hidden="true"></span>
          <span>Cancel</span>
        </button>
        <div class="relative">
          <select
            v-model="selectionCandidate"
            :disabled="isSaving || !stagedAvailableAccounts.length || !isEditing"
            @change="handleAddAccount"
            class="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-600 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/30 disabled:cursor-not-allowed disabled:border-gray-100 disabled:text-gray-300 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-200"
          >
            <option value="">Add account…</option>
            <option
              v-for="account in stagedAvailableAccounts"
              :key="account.account_id"
              :value="account.account_id"
            >
              {{ accountOptionLabel(account) }}
            </option>
          </select>
          <span
            v-if="isSaving"
            class="absolute -right-3 -top-3 i-carbon-circle-dash animate-spin text-primary"
            aria-label="Saving"
          ></span>
        </div>
      </div>
    </header>

    <section
      class="mt-6 rounded-2xl border border-gray-100 bg-white/80 p-4 dark:border-gray-800 dark:bg-gray-900/60"
    >
      <dl class="grid gap-4 sm:grid-cols-2">
        <div>
          <dt class="text-xs uppercase tracking-wide text-gray-400">Total balance</dt>
          <dd class="mt-1 text-2xl font-semibold text-blue-950 dark:text-blue-100">
            {{ formatAccounting(totalBalance) }}
          </dd>
        </div>
        <div>
          <dt class="text-xs uppercase tracking-wide text-gray-400">Upcoming 7 days</dt>
          <dd
            class="mt-1 flex items-center gap-2 text-lg font-medium"
            :class="upcomingClass(totalUpcoming)"
          >
            <span class="i-carbon-calendar text-base" aria-hidden="true"></span>
            <span>{{ formatUpcoming(totalUpcoming) }}</span>
            <span
              v-if="remindersLoading"
              class="i-carbon-circle-dash animate-spin text-xs"
              aria-label="Loading reminders"
            ></span>
          </dd>
        </div>
      </dl>
      <p class="mt-3 text-xs text-gray-400">
        {{ isEditing ? 'Staged' : 'Selected' }} {{ stagedSelection.length }} /
        {{ maxSelection }} accounts
      </p>
      <p v-if="isEditing" class="text-[11px] text-amber-600">
        Changes are staged until you click Save.
      </p>
    </section>

    <section class="mt-6">
      <h4 class="text-xs uppercase tracking-wide text-gray-400">Snapshot selection</h4>
      <div class="mt-2 flex flex-wrap gap-2">
        <span
          v-for="account in stagedAccounts"
          :key="account.account_id"
          class="inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/5 px-3 py-1 text-xs text-primary dark:border-primary/60"
        >
          <span class="i-carbon-chart-multitype text-sm" aria-hidden="true"></span>
          <span class="max-w-[140px] truncate">{{ account.name }}</span>
          <button
            type="button"
            class="i-carbon-close text-xs text-primary/80 transition hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="!isEditing || isSaving"
            @click="handleRemoveAccount(account.account_id)"
            :aria-label="`Remove ${account.name} from snapshot`"
          ></button>
        </span>
        <p v-if="!stagedAccounts.length && !isLoading" class="text-sm text-gray-400">
          Choose accounts to populate the snapshot preview.
        </p>
      </div>
    </section>

    <section class="mt-6">
      <div v-if="isLoading" class="space-y-3">
        <div
          v-for="s in 3"
          :key="`snapshot-skeleton-${s}`"
          class="h-20 animate-pulse rounded-2xl bg-gray-100 dark:bg-gray-800/70"
        ></div>
      </div>
      <div
        v-else-if="!stagedAccounts.length"
        class="rounded-2xl border border-dashed border-gray-300 bg-white/40 p-6 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-900/40 dark:text-gray-400"
      >
        No accounts selected yet. Use the control above to build your snapshot.
      </div>
      <div v-else class="space-y-4">
        <article
          v-for="account in stagedAccounts"
          :key="account.account_id"
          class="overflow-hidden rounded-2xl border border-gray-100 bg-white p-4 shadow-sm transition hover:border-primary/40 dark:border-gray-800 dark:bg-gray-900"
        >
          <button
            type="button"
            class="flex w-full items-center justify-between gap-4 rounded-xl text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.99] dark:focus-visible:ring-offset-gray-900"
            @click="toggleDetails(account.account_id)"
            @keydown.enter.prevent="toggleDetails(account.account_id)"
            @keydown.space.prevent="toggleDetails(account.account_id)"
            :aria-expanded="openAccountId === account.account_id"
            :aria-pressed="openAccountId === account.account_id"
            :aria-label="`Toggle details for ${account.name}`"
          >
            <div class="flex flex-col gap-1">
              <span class="text-sm font-semibold text-blue-950 dark:text-blue-100">{{
                account.name
              }}</span>
              <span class="text-xs text-gray-500 dark:text-gray-400">{{
                account.institution_name || '—'
              }}</span>
              <span class="text-[10px] uppercase tracking-wide text-gray-400">
                Tap to view recent activity
              </span>
            </div>
            <div class="flex flex-col items-end gap-2 text-right">
              <span class="font-mono text-lg font-semibold text-blue-900 dark:text-blue-100">
                {{ formatAccounting(account.balance) }}
              </span>
              <span
                class="inline-flex items-center gap-1 rounded-full text-xs font-medium"
                :class="upcomingPillClass(netUpcoming(account))"
              >
                <span class="i-carbon-calendar text-sm" aria-hidden="true"></span>
                {{ formatUpcoming(netUpcoming(account)) }}
              </span>
            </div>
          </button>
          <div
            v-if="openAccountId === account.account_id"
            class="mt-4 grid gap-4 border-t border-gray-100 pt-4 dark:border-gray-800 sm:grid-cols-2"
          >
            <div>
              <h5 class="text-xs font-semibold uppercase tracking-wide text-gray-400">
                Upcoming (next 7 days)
              </h5>
              <ul class="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                <li v-if="!upcomingForAccount(account).length" class="italic text-gray-400">
                  No reminders due.
                </li>
                <li
                  v-for="(reminder, idx) in upcomingForAccount(account)"
                  :key="reminder.id || reminder.description + reminder.next_due_date + idx"
                  class="flex items-start justify-between gap-3 rounded-xl bg-gray-50 px-3 py-2 dark:bg-gray-800/60"
                >
                  <div>
                    <p class="font-semibold text-gray-700 dark:text-gray-200">
                      {{ reminder.description }}
                    </p>
                    <p
                      v-if="reminder.next_due_date"
                      class="text-[10px] uppercase tracking-wide text-gray-400"
                    >
                      {{ reminder.next_due_date }}
                    </p>
                  </div>
                  <span class="font-mono" :class="upcomingClass(reminder.amount)">
                    {{ formatUpcoming(reminder.amount) }}
                  </span>
                </li>
              </ul>
            </div>
            <div>
              <h5 class="text-xs font-semibold uppercase tracking-wide text-gray-400">
                Recent activity
              </h5>
              <ul class="mt-2 space-y-2 text-xs text-gray-600 dark:text-gray-300">
                <li v-if="recentTxs[account.account_id] === undefined" class="italic text-gray-400">
                  Loading…
                </li>
                <li
                  v-else-if="recentTxs[account.account_id]?.length === 0"
                  class="italic text-gray-400"
                >
                  No recent transactions.
                </li>
                <li
                  v-for="tx in recentTxs[account.account_id]"
                  :key="tx.id || tx.transaction_id"
                  class="flex items-center justify-between gap-3 rounded-xl bg-gray-50 px-3 py-2 transition hover:bg-gray-100 focus-visible:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-50 active:scale-[0.99] dark:bg-gray-800/60 dark:hover:bg-gray-800 dark:focus-visible:ring-offset-gray-900"
                  role="button"
                  tabindex="0"
                  data-testid="account-snapshot-transaction"
                  @click="handleTransactionClick(tx, account.account_id)"
                  @keydown.enter.prevent="handleTransactionClick(tx, account.account_id)"
                  @keydown.space.prevent="handleTransactionClick(tx, account.account_id)"
                  :aria-label="`View transaction ${tx.name || tx.merchant_name || tx.description || ''}`"
                >
                  <div class="flex-1 truncate">
                    <p class="truncate font-medium text-gray-700 dark:text-gray-200">
                      {{ tx.name || tx.merchant_name || tx.description }}
                    </p>
                    <p class="text-[10px] uppercase tracking-wide text-gray-400">
                      {{ tx.date || tx.transaction_date || '' }}
                    </p>
                  </div>
                  <span class="font-mono" :class="upcomingClass(tx.amount)">
                    {{ formatAccounting(tx.amount) }}
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useSnapshotAccounts } from '@/composables/useSnapshotAccounts.js'
import { fetchRecentTransactions } from '@/api/transactions'

const selectionCandidate = ref('')
const openAccountId = ref(null)
const recentTxs = reactive({})
const isEditing = ref(false)
const stagedSelection = ref([])
const router = useRouter()

const {
  accounts,
  selectedIds,
  reminders,
  metadata,
  maxSelection,
  isLoading,
  isSaving,
  remindersLoading,
  error,
  refreshSnapshot,
  refreshReminders,
  persistSelection,
} = useSnapshotAccounts(10, false)

const stagedAccounts = computed(() =>
  stagedSelection.value
    .map((id) => accounts.value.find((account) => account.account_id === id))
    .filter(Boolean),
)

const stagedAvailableAccounts = computed(() =>
  accounts.value.filter((account) => !stagedSelection.value.includes(account.account_id)),
)

const hasStagedChanges = computed(() => !areIdsEqual(stagedSelection.value, selectedIds.value))

watch(
  selectedIds,
  (ids) => {
    if (!isEditing.value) {
      stagedSelection.value = (ids || []).slice(0, maxSelection.value)
    }
  },
  { immediate: true },
)

watch(
  stagedSelection,
  (ids) => {
    if (openAccountId.value && !ids.includes(openAccountId.value)) {
      openAccountId.value = null
    }
  },
  { deep: false },
)

const errorMessage = computed(() => {
  if (!error.value) return ''
  return error.value.message || String(error.value)
})

function areIdsEqual(a = [], b = []) {
  if (a.length !== b.length) return false
  return a.every((val, idx) => val === b[idx])
}

function accountOptionLabel(account) {
  if (!account) return ''
  const institution = account.institution_name ? `${account.institution_name} · ` : ''
  return `${institution}${account.name}`
}

function handleAddAccount() {
  if (!selectionCandidate.value || !isEditing.value) return
  const candidate = selectionCandidate.value
  selectionCandidate.value = ''
  if (stagedSelection.value.includes(candidate)) return

  const limit = maxSelection.value
  if (stagedSelection.value.length >= limit) {
    const next = stagedSelection.value.slice(1)
    stagedSelection.value = [...next, candidate]
  } else {
    stagedSelection.value = [...stagedSelection.value, candidate]
  }
}

function handleRemoveAccount(accountId) {
  if (!isEditing.value) return
  stagedSelection.value = stagedSelection.value.filter((id) => id !== accountId)
  if (openAccountId.value === accountId) {
    openAccountId.value = null
  }
}

function startEditing() {
  stagedSelection.value = selectedIds.value.slice(0, maxSelection.value)
  isEditing.value = true
}

function cancelEditing() {
  stagedSelection.value = selectedIds.value.slice(0, maxSelection.value)
  selectionCandidate.value = ''
  isEditing.value = false
}

async function saveEditing() {
  if (!hasStagedChanges.value) {
    isEditing.value = false
    return
  }

  try {
    await persistSelection(stagedSelection.value)
    if (stagedSelection.value.length) {
      refreshReminders()
    }
    isEditing.value = false
  } catch (err) {
    console.error('Failed to save snapshot selection', err)
  }
}

async function handleRefresh() {
  await refreshSnapshot()
  if (selectedIds.value.length) {
    refreshReminders()
  }
}

function formatAccounting(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return num < 0 ? `($${abs})` : `$${abs}`
}

function formatUpcoming(val) {
  const num = parseFloat(val || 0)
  const abs = Math.abs(num).toLocaleString('en-US', {
    style: 'decimal',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  if (num === 0) return '$0.00'
  return num > 0 ? `+$${abs}` : `-$${abs}`
}

function upcomingClass(val) {
  const num = parseFloat(val || 0)
  if (num > 0) return 'text-green-600 dark:text-green-400'
  if (num < 0) return 'text-red-500 dark:text-red-400'
  return 'text-gray-500 dark:text-gray-300'
}

function upcomingPillClass(val) {
  // Pill palettes: emerald for positive (success), rose for negative (risk), blue for neutral/info.
  const palette = {
    positive: [
      'bg-emerald-50',
      'text-emerald-800',
      'ring-1',
      'ring-emerald-200',
      'dark:bg-emerald-900/60',
      'dark:text-emerald-200',
      'dark:ring-emerald-700/60',
    ],
    negative: [
      'bg-rose-50',
      'text-rose-800',
      'ring-1',
      'ring-rose-200',
      'dark:bg-rose-900/60',
      'dark:text-rose-200',
      'dark:ring-rose-700/60',
    ],
    neutral: [
      'bg-blue-50',
      'text-blue-800',
      'ring-1',
      'ring-blue-200',
      'dark:bg-blue-900/60',
      'dark:text-blue-100',
      'dark:ring-blue-700/60',
    ],
  }

  const base = [
    'faded-upcoming',
    'font-mono',
    'transition-colors',
    'px-2.5',
    'py-1',
    'leading-tight',
  ]
  const num = parseFloat(val || 0)
  if (num > 0) return [...base, ...palette.positive]
  if (num < 0) return [...base, ...palette.negative]
  return [...base, ...palette.neutral]
}

const totalBalance = computed(() =>
  stagedAccounts.value.reduce((sum, account) => sum + parseFloat(account.balance || 0), 0),
)

const totalUpcoming = computed(() =>
  stagedAccounts.value.reduce((sum, account) => sum + netUpcoming(account), 0),
)

function netUpcoming(account) {
  const list = upcomingForAccount(account)
  return list.reduce((sum, tx) => sum + (parseFloat(tx.amount) || 0), 0)
}

function upcomingForAccount(account) {
  if (!account) return []
  if (Array.isArray(reminders.value)) {
    return reminders.value.filter((tx) => tx.account_id === account.account_id)
  }
  return reminders.value[account.account_id] || []
}

function toggleDetails(accountId) {
  const nextOpen = openAccountId.value === accountId ? null : accountId
  openAccountId.value = nextOpen
  if (nextOpen && !(accountId in recentTxs)) {
    recentTxs[accountId] = undefined
    fetchRecentTransactions(accountId, 3)
      .then((res) => {
        let txs = []
        if (Array.isArray(res?.transactions)) {
          txs = res.transactions
        } else if (Array.isArray(res?.data?.transactions)) {
          txs = res.data.transactions
        } else if (Array.isArray(res?.data)) {
          txs = res.data
        }
        recentTxs[accountId] = txs
      })
      .catch(() => {
        recentTxs[accountId] = []
      })
  }
}

/**
 * Navigate to the Transactions table mirroring the modal drill-down.
 *
 * @param {Record<string, unknown>} tx - Transaction selected within the widget.
 * @param {string} fallbackAccountId - Account identifier to apply when the
 *   transaction payload omits it.
 */
function handleTransactionClick(tx, fallbackAccountId) {
  const txid = tx?.transaction_id ?? tx?.id
  const accountId = tx?.account_id ?? tx?.accountId ?? fallbackAccountId
  const query = {}

  if (txid !== undefined && txid !== null && txid !== '') {
    query.promote = String(txid)
  }

  if (accountId !== undefined && accountId !== null && accountId !== '') {
    query.account_id = String(accountId)
  }

  if (Object.keys(query).length) {
    router.push({ name: 'Transactions', query })
  } else {
    router.push({ name: 'Transactions' })
  }
}
</script>

<style scoped>
.faded-upcoming {
  opacity: 0.8;
  font-style: italic;
}

.faded-upcoming:hover,
.faded-upcoming:focus {
  opacity: 1;
  font-style: normal;
}
</style>
