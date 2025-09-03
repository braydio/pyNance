<template>
  <transition name="modal-fade-slide" @after-leave="emitClose">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4 py-6"
      @click.self="emitClose"
      @keyup.esc="emitClose"
      tabindex="0"
    >
      <div
        class="relative w-full max-w-3xl mx-auto p-0 rounded-2xl shadow-2xl bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)]/60 animate-fadeInUp flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Transactions Modal"
        style="min-height: 220px"
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
              >Income</span
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
        <!-- END SUMMARY BAR -->
        <div class="flex-1 p-6 overflow-y-auto max-h-[65vh]">
          <ModalTransactionsDisplay
            :transactions="transactions"
            :title-date="kind === 'date' ? subtitle : ''"
            :show-date-column="kind === 'category' && showDateColumn"
            :show-category-visuals="!(kind === 'category' && hideCategoryVisuals)"
            @row-click="onRowClick"
          />
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import ModalTransactionsDisplay from '../tables/ModalTransactionsDisplay.vue'
import { formatAmount } from '@/utils/format'

// Modal dialog displaying a list of transactions with a summary bar and optional prominently displayed subtitle.

const props = defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  subtitle: { type: String, default: '' },
  kind: { type: String, default: 'date' }, // 'date' | 'category'
  showDateColumn: { type: Boolean, default: true },
  hideCategoryVisuals: { type: Boolean, default: true },
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

const titleLabel = computed(() =>
  props.kind === 'category' ? 'Category Transactions' : 'Transactions',
)
const subtitlePrefix = computed(() => (props.kind === 'category' ? 'Category' : 'Date'))

// --- SUMMARY COMPUTATION ---
const summary = computed(() => {
  let expense = 0
  let income = 0
  if (Array.isArray(props.transactions)) {
    props.transactions.forEach((tx) => {
      const amt = Number(tx.amount) || 0
      if (amt < 0) expense += amt
      else income += amt
    })
  }
  return {
    expense,
    income,
    net: income + expense,
  }
})

function onRowClick(tx) {
  const txid = tx?.transaction_id || tx?.id
  if (txid) {
    router.push({ name: 'Transactions', query: { txid } })
  } else {
    router.push({ name: 'Transactions' })
  }
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
