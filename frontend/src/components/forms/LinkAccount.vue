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
                <span v-if="selectedSummary" class="block text-xs text-muted mt-1">
                  Selected: {{ selectedSummary }}
                </span>
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

          <div class="mt-4 space-y-6">
            <section>
              <div class="flex items-center justify-between gap-3">
                <p class="text-xs uppercase tracking-wide text-muted">Step 1</p>
                <p class="text-xs text-muted">Choose product scope</p>
              </div>
              <PlaidProductScopeSelector
                :model-value="selectedProducts"
                @update:model-value="updateSelectedProducts"
              />
            </section>

            <section class="border-t border-[var(--divider)] pt-4">
              <div class="flex items-center justify-between gap-3">
                <p class="text-xs uppercase tracking-wide text-muted">Step 2</p>
                <p class="text-xs text-muted">Connect with Plaid</p>
              </div>
              <p class="text-sm text-muted mt-2">
                Each account link requires at least one product scope.
              </p>
              <div class="flex flex-wrap items-center justify-end gap-2 mt-4">
                <UiButton variant="outline" class="btn-sm" @click="closeDialog">Cancel</UiButton>
                <LinkProviderLauncher
                  :selected-products="selectedProducts"
                  :user-id="userID"
                  @refresh="handleRefresh"
                >
                  <template #default="{ linkPlaid, loading, isDisabled }">
                    <UiButton
                      variant="primary"
                      pill
                      :class="{ 'opacity-50 cursor-not-allowed': isDisabled }"
                      :disabled="isDisabled"
                      @click="linkPlaid"
                    >
                      {{ loading ? 'Linking…' : 'Link With Selected Scope' }}
                    </UiButton>
                  </template>
                </LinkProviderLauncher>
              </div>
            </section>
          </div>
        </div>
      </div>
    </transition>
  </Card>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, toRefs, watch } from 'vue'
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import PlaidProductScopeSelector from '@/components/forms/PlaidProductScopeSelector.vue'
import LinkProviderLauncher from '@/components/forms/LinkProviderLauncher.vue'

const props = defineProps({
  selectedProducts: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['refreshAccount', 'update:selectedProducts'])
const { selectedProducts } = toRefs(props)
const showDialog = ref(false)
const userID = import.meta.env.VITE_USER_ID_PLAID || ''
const dialogRef = ref(null)
const closeButtonRef = ref(null)
const previousFocusElement = ref(null)
const previousBodyOverflow = ref('')

const selectedSummary = computed(() =>
  selectedProducts.value.length ? selectedProducts.value.map(formatProductLabel).join(', ') : '',
)

/**
 * Emit updates to the selected Plaid products.
 *
 * @param {string[]} products - Updated list of selected products.
 */
function updateSelectedProducts(products) {
  emit('update:selectedProducts', products)
}

/**
 * Format Plaid product identifiers for human-readable labels.
 *
 * @param {string} product - Plaid product identifier.
 * @returns {string} Readable product label.
 */
function formatProductLabel(product) {
  return product.charAt(0).toUpperCase() + product.slice(1)
}

// Accessibility focus trapping
const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

function getFocusableElements() {
  if (!dialogRef.value) return []
  return Array.from(dialogRef.value.querySelectorAll(focusableSelector)).filter(
    (el) => !el.hasAttribute('disabled') && el.getAttribute('aria-hidden') !== 'true',
  )
}

function trapFocus(event) {
  if (event.key !== 'Tab') return
  const focusables = getFocusableElements()
  if (!focusables.length) return

  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  const active = document.activeElement

  if (event.shiftKey && active === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && active === last) {
    event.preventDefault()
    first.focus()
  }
}

function handleDialogKeydown(event) {
  if (event.key === 'Escape') {
    event.preventDefault()
    closeDialog()
  } else {
    trapFocus(event)
  }
}

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

// Manage focus/scroll locking when dialog toggles
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
