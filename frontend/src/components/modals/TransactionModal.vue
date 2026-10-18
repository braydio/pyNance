<template>
  <transition name="modal-fade-slide" @after-leave="emitClose">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4 py-6"
      @click.self="emitClose"
    >
      <div
        ref="dialogRef"
        class="relative w-full max-w-5xl mx-auto p-0 rounded-2xl shadow-2xl bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)]/60 animate-fadeInUp flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Transactions Modal"
        tabindex="-1"
        style="min-height: 220px; max-height: calc(100dvh - 2rem)"
      >
        <!-- Header -->
        <div
          class="relative flex items-center justify-between px-5 py-4 bg-[var(--color-bg-dark)] border-b-2 border-[var(--color-accent-cyan)]/50 shadow-lg"
        >
          <div class="flex flex-col gap-1">
            <h2
              class="flex items-center gap-2 text-xl font-extrabold text-[var(--color-accent-cyan)] tracking-wide"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <circle cx="12" cy="12" r="10" />
                <path d="M7 12h10M12 7v10" stroke-linecap="round" />
              </svg>
              {{ titleLabel }}
            </h2>
            <div v-if="subtitle" class="inline-flex items-center gap-2">
              <span class="text-xs uppercase tracking-widest text-[var(--color-text-muted)]">{{
                subtitlePrefix
              }}</span>
              <span
                class="px-2 py-0.5 rounded-lg text-base font-semibold bg-[var(--color-accent-cyan)]/15 text-[var(--color-text-light)] border border-[var(--color-accent-cyan)]/40"
              >
                {{ subtitle }}
              </span>
            </div>
          </div>
          <button
            type="button"
            class="relative inline-flex items-center justify-center w-9 h-9 rounded-full text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/40 hover:bg-[var(--color-accent-cyan)] hover:text-[var(--color-bg-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-cyan)] transition"
            @click="emitClose"
            aria-label="Close Transactions Modal"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="2"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
            </svg>
          </button>
        </div>
        <!-- SUMMARY BAR -->
        <div
          class="flex gap-8 justify-center items-center px-8 py-4 bg-gradient-to-r from-[var(--color-bg-dark)]/60 via-[var(--color-bg-secondary)]/60 to-[var(--color-bg-dark)]/60 border-b border-[var(--color-accent-purple)]/30 rounded-b-xl"
        >
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1"
              >Expense</span
            >
            <span class="text-xl font-extrabold text-[var(--color-accent-red)] drop-shadow-sm">{{
              formatAmount(summary.expense)
            }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1"
              >Income<span v-if="flowSummary.classified" class="normal-case tracking-normal">
                (excl. transfers)</span
              ></span
            >
            <span class="text-xl font-extrabold text-[var(--color-accent-green)] drop-shadow-sm">{{
              formatAmount(summary.income)
            }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1"
              >Net</span
            >
            <span
              :class="[
                'text-xl font-extrabold drop-shadow-sm',
                summary.net > 0
                  ? 'text-[var(--color-accent-green)]'
                  : summary.net < 0
                    ? 'text-[var(--color-accent-red)]'
                    : 'text-[var(--color-text-light)]',
              ]"
            >
              {{ formatAmount(summary.net) }}
            </span>
          </div>
        </div>
        <!-- Cash movement that is not income or spending, kept visible but out of Net -->
        <div
          v-if="movementLines.length || notices.length"
          class="px-8 py-2 text-xs text-[var(--color-text-muted)] border-b border-[var(--color-accent-purple)]/20"
          data-testid="movement-summary"
        >
          <ul v-if="movementLines.length" class="flex flex-wrap justify-center gap-x-6 gap-y-1">
            <li v-for="line in movementLines" :key="line">{{ line }}</li>
          </ul>
          <p
            v-for="note in notices"
            :key="note"
            class="mt-1 text-center text-[var(--color-accent-yellow)]"
            role="status"
          >
            {{ note }}
          </p>
        </div>
        <!-- END SUMMARY BAR -->
        <div class="flex-1 min-h-0 p-6 overflow-y-auto">
          <ModalTransactionsDisplay
            :transactions="transactions"
            :title-date="''"
            :show-date-column="showDateColumn"
            :show-category-visuals="showCategoryVisuals"
            :details-header="detailsHeader"
            :primary-field="primaryField"
            @row-click="onRowClick"
          />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { onMounted, nextTick, computed, ref } from 'vue'
import { useModalA11y } from '@/composables/useModalA11y'
import { useRouter } from 'vue-router'
import ModalTransactionsDisplay from '../tables/ModalTransactionsDisplay.vue'
import { formatAmount } from '@/utils/format'
import { disagreesWithChart, summarizeFlows } from '@/utils/flowSummary'

/**
 * Modal dialog displaying a list of transactions with a summary bar and optional subtitle.
 */

const props = defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  subtitle: { type: String, default: '' },
  subtitlePrefix: { type: String, default: '' }, // Override prefix (e.g., 'Merchant')
  kind: { type: String, default: 'date' }, // 'date' | 'category' | 'merchant'
  showDateColumn: { type: Boolean, default: true },
  hideCategoryVisuals: { type: Boolean, default: true },
  // Chart values for the same day ({income, expenses, net}); a disagreement is surfaced, never hidden.
  reference: { type: Object, default: null },
  // Server-provided caveat, e.g. only part of a very large day was loaded.
  notice: { type: String, default: '' },
})

const dialogRef = ref(null)
useModalA11y({
  dialogRef,
  active: computed(() => props.show),
  onEscape: () => {
    emitClose()
    return true
  },
})

const emit = defineEmits(['close'])
const router = useRouter()

onMounted(() => {
  nextTick(() => {
    document.querySelector('.fixed[tabindex="0"]')?.focus()
  })
})

function emitClose() {
  emit('close')
}

const titleLabel = computed(() => {
  if (props.kind === 'category') return 'Category Transactions'
  if (props.kind === 'merchant') return 'Merchant Transactions'
  return 'Transactions'
})
const subtitlePrefix = computed(
  () =>
    props.subtitlePrefix ||
    (props.kind === 'category' ? 'Category' : props.kind === 'merchant' ? 'Merchant' : 'Date'),
)

/**
 * Ensure category visuals remain visible unless explicitly hidden by the
 * consumer. Non-category modals always render visuals.
 */
const showCategoryVisuals = computed(() => props.kind !== 'category' || !props.hideCategoryVisuals)
const detailsHeader = computed(() => (props.kind === 'merchant' ? 'Description' : 'Merchant'))
const primaryField = computed(() => (props.kind === 'merchant' ? 'description' : 'merchant_name'))

// --- SUMMARY COMPUTATION ---
const flowSummary = computed(() => summarizeFlows(props.transactions))

// Income/Expense/Net use the backend's economic classification; feeds without one keep the legacy
// sign split so category and merchant drill-downs behave as before.
const summary = computed(() => {
  if (flowSummary.value.classified) {
    const { income, expense, net } = flowSummary.value
    return { income, expense, net }
  }
  let expense = 0
  let income = 0
  if (Array.isArray(props.transactions)) {
    props.transactions.forEach((tx) => {
      const amt = Number(tx.amount) || 0
      if (amt < 0) expense += amt
      else income += amt
    })
  }
  return { expense, income, net: income + expense }
})

const movementLines = computed(() => {
  const f = flowSummary.value
  if (!f.classified) return []
  const lines = []
  if (f.refunds) lines.push(`Refunds ${formatAmount(f.refunds)} (in Net)`)
  if (f.transferCount) {
    lines.push(
      `Transfers in ${formatAmount(f.transfersIn)} / out ${formatAmount(-f.transfersOut)} (${f.transferCount}, not in Net)`,
    )
  }
  if (f.debtCount)
    lines.push(`Debt payments ${formatAmount(-f.debtPayments)} (${f.debtCount}, not in Net)`)
  if (f.investmentCount) {
    lines.push(`Investment moves ${formatAmount(f.investment)} (${f.investmentCount}, not in Net)`)
  }
  if (f.unclassifiedCount) {
    lines.push(
      `Needs classification: ${f.unclassifiedCount} (${formatAmount(f.unclassifiedAmount)}, not in Net)`,
    )
  }
  return lines
})

const notices = computed(() => {
  const list = []
  if (props.notice) list.push(props.notice)
  if (flowSummary.value.pendingCount) {
    list.push(`${flowSummary.value.pendingCount} pending not included in totals`)
  }
  if (disagreesWithChart(flowSummary.value, props.reference)) {
    list.push('These totals differ from the chart for this day; some activity may not be loaded.')
  }
  return list
})

/**
 * Navigate to the Transactions route, pre-populating highlight and edit targets
 * based on the clicked transaction.
 *
 * @param {Record<string, unknown>} tx - The transaction that was clicked.
 */
function onRowClick(tx) {
  const txid = tx?.transaction_id ?? tx?.id
  const accountId = tx?.account_id ?? tx?.accountId
  const query = {}

  if (txid !== undefined && txid !== null && txid !== '') query.promote = String(txid)
  if (txid !== undefined && txid !== null && txid !== '') query.txid = String(txid)
  if (accountId !== undefined && accountId !== null && accountId !== '')
    query.account_id = String(accountId)

  if (Object.keys(query).length) router.push({ name: 'Transactions', query })
  else router.push({ name: 'Transactions' })

  emitClose()
}
</script>

<style scoped>
@keyframes modalFadeInUp {
  from {
    opacity: 0;
    transform: translateY(48px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: none;
  }
}

@keyframes modalFadeOutDown {
  from {
    opacity: 1;
    transform: none;
  }

  to {
    opacity: 0;
    transform: translateY(48px) scale(0.98);
  }
}

.modal-fade-slide-enter-active {
  animation: modalFadeInUp 0.45s cubic-bezier(0.45, 1.5, 0.62, 1) both;
}

.modal-fade-slide-leave-active {
  animation: modalFadeOutDown 0.35s cubic-bezier(0.55, 0.06, 0.68, 0.19) both;
}
</style>
