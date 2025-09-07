<template>
  <select
    :value="modelValue"
    @change="onChange"
    class="input px-2 py-1 rounded border border-[var(--divider)] bg-[var(--theme-bg)] text-[var(--color-text-light)]"
    data-testid="account-select"
  >
    <option value="">All Accounts</option>
    <option v-for="acct in accounts" :key="acct.account_id" :value="acct.account_id">
      {{ acct.name }}
    </option>
  </select>
</template>

<script setup>
/**
 * Dropdown selector for filtering transactions by account.
 * Fetches account list on mount and exposes v-model for the selected account id.
 */
import { ref, onMounted } from 'vue'

import api from '@/services/api'


const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])
const accounts = ref([])

function onChange(e) {
  emit('update:modelValue', e.target.value)
}

onMounted(async () => {
  try {

    const data = await api.getAccounts()

    accounts.value = data.accounts || []
  } catch (err) {
    // silently ignore fetch errors for selector
    console.error('Failed to load accounts', err)
  }
})
</script>
