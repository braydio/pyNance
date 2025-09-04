<template>
  <div class="space-y-4" data-testid="account-actions-sidebar">
    <LinkAccount :selected-products="selectedProducts" @manual-token-click="toggleManualToken" />
    <TokenUpload v-if="showTokenForm" @cancel="toggleManualToken" class="w-full" />
    <TogglePanel v-model="showPlaidRefresh" title="Refresh Plaid Accounts">
      <RefreshPlaidControls />
    </TogglePanel>
    <TogglePanel v-model="showTellerRefresh" title="Refresh Teller Accounts">
      <RefreshTellerControls />
    </TogglePanel>
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
import TogglePanel from '@/components/ui/TogglePanel.vue'
import RefreshPlaidControls from '@/components/widgets/RefreshPlaidControls.vue'
import RefreshTellerControls from '@/components/widgets/RefreshTellerControls.vue'

const selectedProducts = ref([])
const showTokenForm = ref(false)
const showPlaidRefresh = ref(false)
const showTellerRefresh = ref(false)

function toggleManualToken() {
  showTokenForm.value = !showTokenForm.value
}
</script>
