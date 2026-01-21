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
        <div
          ref="dialogRef"
          class="link-dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="link-account-title"
          aria-describedby="link-account-description"
        >
          <header class="flex items-start justify-between gap-3">
            <div>
              <p class="text-xs uppercase tracking-wide text-muted">Scope Selection</p>
              <h3 id="link-account-title" class="text-lg font-semibold">Select an Account Type</h3>
              <p id="link-account-description" class="text-sm text-muted">
                Select from the following classifications for your new account link.
              </p>
            </div>
            <button
              ref="closeButtonRef"
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
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import PlaidProductScopeSelector from '@/components/forms/PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

const selectedProducts = ref(['transactions'])
const showDialog = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''
const dialogRef = ref(null)
const closeButtonRef = ref(null)
const previousFocusElement = ref(null)
const previousBodyOverflow = ref('')

const emit = defineEmits(['refreshAccount'])

const focusableSelector =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * Returns the focusable elements inside the dialog for keyboard trapping.
 * @returns {HTMLElement[]} Focusable elements in the dialog.
 */
function getFocusableElements() {
  if (!dialogRef.value) {
    return []
  }

  return Array.from(dialogRef.value.querySelectorAll(focusableSelector)).filter(
    (element) => !element.hasAttribute('disabled') && element.getAttribute('aria-hidden') !== 'true',
  )
}

/**
 * Keeps focus within the dialog when using Tab/Shift+Tab.
 * @param {KeyboardEvent} event Keyboard event from the document.
 */
function trapFocus(event) {
  if (event.key !== 'Tab') {
    return
  }

  const focusableElements = getFocusableElements()
  if (focusableElements.length === 0) {
    return
  }

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]
  const activeElement = document.activeElement

  if (event.shiftKey && activeElement === firstElement) {
    event.preventDefault()
    lastElement.focus()
    return
  }

  if (!event.shiftKey && activeElement === lastElement) {
    event.preventDefault()
    firstElement.focus()
  }
}

/**
 * Handles keyboard interactions while the dialog is open.
 * @param {KeyboardEvent} event Keyboard event from the document.
 */
function handleDialogKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeDialog()
    return
  }

  trapFocus(event)
}

/**
 * Opens the dialog and prepares focus/scroll management.
 */
function openDialog() {
  showDialog.value = true
}

/**
 * Closes the dialog and restores focus/scroll state.
 */
function closeDialog() {
  showDialog.value = false
}

/**
 * Emits refresh action and closes the dialog.
 */
function handleRefresh() {
  emit('refreshAccount')
  closeDialog()
}

watch(showDialog, async (isOpen) => {
  if (isOpen) {
    previousFocusElement.value = document.activeElement
    previousBodyOverflow.value = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handleDialogKeydown)
    await nextTick()
    closeButtonRef.value?.focus()
  } else {
    document.removeEventListener('keydown', handleDialogKeydown)
    document.body.style.overflow = previousBodyOverflow.value
    const focusTarget = previousFocusElement.value
    if (focusTarget && typeof focusTarget.focus === 'function') {
      focusTarget.focus()
    }
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleDialogKeydown)
  document.body.style.overflow = previousBodyOverflow.value
})
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
