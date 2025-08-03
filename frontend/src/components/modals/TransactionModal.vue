<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur px-4 py-6"
    @click.self="emitClose" @keyup.esc="emitClose" tabindex="0">
    <div
      class="relative w-full max-w-3xl mx-auto rounded-2xl shadow-2xl bg-gradient-to-br from-violet-950/70 via-slate-900/90 to-blue-950/90 border-2 border-violet-400/40 animate-fadeInUp flex flex-col"
      style="min-height: 220px;">
      <!-- Header -->
      <div
        class="flex items-center justify-between px-8 py-5 bg-gradient-to-r from-violet-700/70 via-slate-900/70 to-blue-800/70 border-b-2 border-violet-500/40 shadow-lg backdrop-blur-xl">
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
        <button class="group p-2 rounded-full hover:bg-violet-600/80 focus:bg-violet-500/80 transition"
          @click="emitClose" aria-label="Close">
          <svg class="w-6 h-6 text-violet-200 group-hover:text-white transition" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
          </svg>
        </button>
      </div>
      <div class="flex-1 p-6 overflow-y-auto max-h-[65vh]">
        <ModalTransactionsDisplay :transactions="transactions" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits, onMounted } from 'vue'
import ModalTransactionsDisplay from '../tables/ModalTransactionsDisplay.vue'

defineProps({
  show: { type: Boolean, default: false },
  transactions: { type: Array, default: () => [] },
  titleDate: { type: String, default: '' }
})

const emit = defineEmits(['close'])
function emitClose() { emit('close') }

onMounted(() => {
  document.querySelector('.fixed[tabindex="0"]')?.focus()
})
</script>

<style scoped>
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(48px) scale(0.98);
  }

  to {
    opacity: 1;
    transform: none;
  }
}

.animate-fadeInUp {
  animation: fadeInUp 0.45s cubic-bezier(.45, 1.5, .62, 1) both;
}
</style>
