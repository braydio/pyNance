<template>
  <Card class="w-full max-w-2xl">
    <div class="flex items-center justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-wide text-muted">New Account</p>
        <p class="text-sm text-muted">Product Scope (Account Type)</p>
      </div>
      <UiButton
        variant="primary"
        class="shadow-lg transition hover:-translate-y-0.5 hover:shadow-xl"
        @click="openDialog"
      >
        Link a New Account with Plaid
      </UiButton>
    </div>

    <transition name="fade">
      <div v-if="showDialog" class="link-dialog-backdrop" @click.self="closeDialog">
        <div class="link-dialog">
          <header class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wide text-muted">Scope Selection</p>
              <h3 class="text-lg font-semibold">Select an Account Type</h3>
              <p class="text-sm text-muted">
                Select from the following classifications for your new account link.
              </p>
            </div>
            <button
              type="button"
              class="text-muted hover:text-[var(--color-accent-cyan)]"
              @click="closeDialog"
              aria-label="Close link dialog"
            >
              ✕
            </button>
          </header>

          <div class="mt-4 space-y-4">
            <PlaidProductScopeSelector v-model="selectedProducts" />
            <div class="flex flex-wrap items-center justify-end gap-2">
              <UiButton variant="outline" class="btn-sm" @click="closeDialog">Cancel</UiButton>
              <LinkProviderLauncher
                :selected-products="selectedProducts"
                :user-id="userID"
                @refresh="handleRefresh"
              />
            </div>
          </div>
        </div>
      </div>
    </transition>
  </Card>
</template>

<script setup>
import { ref } from 'vue'
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import PlaidProductScopeSelector from '@/components/forms/PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

const selectedProducts = ref(['transactions'])
const showDialog = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''

const emit = defineEmits(['refreshAccount'])

function openDialog() {
  showDialog.value = true
}

function closeDialog() {
  showDialog.value = false
}

function handleRefresh() {
  emit('refreshAccount')
  closeDialog()
}
</script>

<style scoped>
.link-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem 1rem;
  background: rgba(0, 0, 0, 0.45);
}

.link-dialog {
  width: min(640px, 100%);
  background: var(--color-bg);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  border-radius: 1rem;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28);
  padding: 1.5rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
