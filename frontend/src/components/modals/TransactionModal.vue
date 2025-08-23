<template>
  <transition name="modal-fade-slide" @after-leave="emitClose">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur px-4 py-6"
      @click.self="emitClose" @keyup.esc="emitClose" tabindex="0">
      <div
        class="relative w-full max-w-3xl mx-auto p-4 rounded-2xl shadow-2xl bg-gradient-to-br from-[var(--color-accent-purple)]/70 via-[var(--color-bg-dark)]/90 to-[var(--color-accent-blue)]/90 border-2 border-[var(--color-accent-purple)]/60 animate-fadeInUp flex flex-col"
        role="dialog" aria-modal="true" aria-label="Transactions Modal" style="min-height: 220px">
        <!-- Header -->
        <div
          class="relative flex items-start justify-between px-2 py-8 bg-gradient-to-r from-[var(--color-accent-purple)]/70 via-[var(--color-bg-dark)]/70 to-[var(--color-accent-blue)]/70 border-b-2 border-[var(--color-accent-purple)]/40 shadow-lg backdrop-blur-xl">
          <div class="flex flex-col">
            <h2 class="flex items-center gap-2 text-xl font-black text-[var(--color-text-light)] uppercase tracking-wider drop-shadow-sm">
              <svg class="w-7 h-7 text-[var(--color-accent-purple)]" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.7" />
                <path d="M7 12h10M12 7v10" stroke-linecap="round" />
              </svg>
              Transactions
            </h2>
            <p v-if="subtitle" class="mt-2 text-lg font-semibold text-[var(--color-accent-purple)] drop-shadow-none">
              {{ subtitle }}
            </p>
          </div>
          <button
            class="absolute top-4 right-4 rounded-full hover:bg-[var(--color-accent-purple)]/80 active:bg-[var(--color-accent-purple)]/90 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-purple)] transition group"
            @click="emitClose" aria-label="Close Transactions Modal">
            <svg class="w-6 h-6 text-[var(--color-accent-purple)] group-hover:text-[var(--color-text-light)] transition" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
            </svg>
          </button>
        </div>
        <!-- SUMMARY BAR -->
        <div
          class="flex gap-8 justify-center items-center px-8 py-4 bg-gradient-to-r from-[var(--color-bg-dark)]/60 via-[var(--color-bg-secondary)]/60 to-[var(--color-bg-dark)]/60 border-b border-[var(--color-accent-purple)]/30 rounded-b-xl">
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1">Expense</span>
            <span class="text-xl font-extrabold text-[var(--color-accent-red)] drop-shadow-sm">{{ formatAmount(summary.expense) }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1">Income</span>
            <span class="text-xl font-extrabold text-[var(--color-accent-green)] drop-shadow-sm">{{ formatAmount(summary.income) }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-[var(--color-text-muted)] uppercase mb-1">Net</span>
            <span :class="[
              'text-xl font-extrabold drop-shadow-sm',
              summary.net > 0
                ? 'text-[var(--color-accent-green)]'
                : summary.net < 0
                  ? 'text-[var(--color-accent-red)]'
                  : 'text-[var(--color-text-light)]'
            ]">
              {{ formatAmount(summary.net) }}
            </span>
          </div>
        </div>
        <!-- END SUMMARY BAR -->
        <div class="flex-1 p-8 overflow-y-auto max-h-[65vh]">
          <ModalTransactionsDisplay :transactions="transactions" />
        </div>
      </div>
    </div>
  </transition>
</template>


<script setup>
import { onMounted, nextTick, computed } from 'vue'
import ModalTransactionsDisplay from '../tables/ModalTransactionsDisplay.vue'
import { formatAmount } from "@/utils/format"

// Modal dialog displaying a list of transactions with a summary bar and optional prominently displayed subtitle.

const props = defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  subtitle: { type: String, default: '' }
})

const emit = defineEmits(['close'])

onMounted(() => {
  nextTick(() => {
    document.querySelector('.fixed[tabindex="0"]')?.focus()
  })
})

function emitClose() { emit('close') }

// --- SUMMARY COMPUTATION ---
const summary = computed(() => {
  let expense = 0
  let income = 0
  if (Array.isArray(props.transactions)) {
    props.transactions.forEach(tx => {
      const amt = Number(tx.amount) || 0
      if (amt < 0) expense += amt
      else income += amt
    })
  }
  return {
    expense,
    income,
    net: income + expense
  }
})
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
  animation: modalFadeInUp 0.45s cubic-bezier(.45, 1.5, .62, 1) both;
}

.modal-fade-slide-leave-active {
  animation: modalFadeOutDown 0.35s cubic-bezier(.55, .06, .68, .19) both;
}
</style>
