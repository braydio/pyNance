<template>
  <div class="space-y-4" data-testid="account-actions-sidebar">
    <LinkAccount v-model:selected-products="selectedProducts" @manual-token-click="toggleManualToken" />
    <TokenUpload v-if="showTokenForm" @cancel="toggleManualToken" class="w-full" />
  </div>
</template>

<script setup>
/**
 * AccountActionsSidebar
 * Sidebar housing account linking and refresh controls.
 */
import { ref } from 'vue'
import LinkAccount from '@/components/forms/LinkAccount.vue'
import TokenUpload from '@/components/forms/TokenUpload.vue'

const selectedProducts = ref([])
const showTokenForm = ref(false)

function toggleManualToken() {
  showTokenForm.value = !showTokenForm.value
}
</script>
