<template>
  <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
    <div class="bg-white rounded-xl shadow-xl w-full max-w-3xl mx-2 relative">
      <div class="flex items-center justify-between px-6 py-4 border-b">
        <h3 class="text-xl font-semibold truncate">{{ title || 'Transactions' }}</h3>
        <button
          class="p-1 rounded hover:bg-gray-100 transition absolute right-3 top-3"
          @click="emitClose"
          aria-label="Close"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="p-4 max-h-[65vh] overflow-y-auto">
        <ModalTransactionsDisplay :transactions="transactions" />
      </div>
      <div class="px-6 py-3 flex justify-end border-t">
        <button
          class="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold"
          @click="emitClose"
        >Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import ModalTransactionsDisplay from '../tables/ModalTransactionsDisplay.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  transactions: { type: Array, default: () => [] }
})

const emit = defineEmits(['close'])

function emitClose() {
  emit('close')
}
</script>

<style scoped>
/* Modal z-index is intentionally high for overlay */
</style>

