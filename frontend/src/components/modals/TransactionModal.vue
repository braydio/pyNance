<template>
  <transition name="modal-fade-slide" @after-leave="emitClose">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur px-4 py-6"
      @click.self="emitClose" @keyup.esc="emitClose" tabindex="0">
      <div
        class="relative w-full max-w-3xl mx-auto rounded-2xl shadow-2xl bg-gradient-to-br from-violet-950/70 via-slate-900/90 to-blue-950/90 border-2 border-violet-400/40 animate-fadeInUp flex flex-col"
        role="dialog" aria-modal="true" aria-label="Transactions Modal" style="min-height: 220px">
        <!-- Header -->
        <div
          class="flex items-center justify-between px-2 py-8 bg-gradient-to-r from-violet-700/70 via-slate-900/70 to-blue-800/70 border-b-2 border-violet-500/40 shadow-lg backdrop-blur-xl">
          <h2 class="flex items-center gap-2 text-xl font-black text-white uppercase tracking-wider drop-shadow-sm">
            <svg class="w-7 h-7 text-violet-300" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke-opacity="0.7" />
              <path d="M7 12h10M12 7v10" stroke-linecap="round" />
            </svg>
            Transactions
            <span v-if="titleDate" class="ml-2 text-violet-200 text-base font-medium normal-case drop-shadow-none">
              ({{ titleDate }})
            </span>
          </h2>
          <button
            class="absolute top-4 right-4 rounded-full hover:bg-violet-600/80 active:bg-violet-700/80 focus:outline-none focus:ring-2 focus:ring-violet-400 transition group"
            @click="emitClose" aria-label="Close Transactions Modal">
            <svg class="w-6 h-6 text-violet-200 group-hover:text-white transition" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
            </svg>
          </button>
        </div>
        <!-- SUMMARY BAR -->
        <div
          class="flex gap-8 justify-center items-center px-8 py-4 bg-gradient-to-r from-violet-950/60 via-slate-900/60 to-blue-950/60 border-b border-violet-800/30 rounded-b-xl">
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-slate-400 uppercase mb-1">Expense</span>
            <span class="text-xl font-extrabold text-red-400 drop-shadow-sm">{{ formatAmount(summary.expense) }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-slate-400 uppercase mb-1">Income</span>
            <span class="text-xl font-extrabold text-green-400 drop-shadow-sm">{{ formatAmount(summary.income) }}</span>
          </div>
          <div class="flex flex-col items-center">
            <span class="text-[10px] tracking-widest text-slate-400 uppercase mb-1">Net</span>
            <span :class="[
              'text-xl font-extrabold drop-shadow-sm',
              summary.net > 0 ? 'text-green-300' : summary.net < 0 ? 'text-red-300' : 'text-slate-300'
            ]">
              {{ formatAmount(summary.net) }}
            </span>
          </div>
        </div>
        <!-- END SUMMARY BAR -->
        <div class="flex-1 p-6 overflow-y-auto max-h-[65vh]">
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

const props = defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  titleDate: { type: String, default: '' }
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
