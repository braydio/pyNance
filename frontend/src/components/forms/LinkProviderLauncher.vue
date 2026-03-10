<template>
  <slot
    :link-plaid="linkPlaid"
    :loading="loading"
    :is-disabled="isDisabled"
    :error-message="errorMessage"
    :status-message="statusMessage"
  />
</template>

<script setup>
import { computed, ref } from 'vue'
import accountLinkApi from '@/api/accounts_link'

let plaidScriptPromise = null

const props = defineProps({
  selectedProducts: {
    type: Array,
    default: () => [],
  },
  userId: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['refresh', 'error'])

const loading = ref(false)
const errorMessage = ref('')
const statusMessage = ref('')
const isDisabled = computed(() => props.selectedProducts.length === 0 || loading.value)

/**
 * Publish a recoverable launcher error for both local rendering and parent-level handling.
 *
 * @param {string} code - Stable error code for analytics and parent UI handling.
 * @param {string} message - User-facing fallback message.
 * @param {unknown} error - Original error payload for console diagnostics.
 */
function publishLauncherError(code, message, error) {
  errorMessage.value = message
  statusMessage.value = ''
  console.error(message, error)
  emit('error', { code, message })
}

/**
 * Ensure the Plaid Link SDK script is available before opening the flow.
 */
async function ensurePlaidScript() {
  if (window.Plaid) return

  if (plaidScriptPromise) {
    return plaidScriptPromise
  }

  const existing = document.querySelector('script[data-plaid-link]')
  if (existing) {
    plaidScriptPromise = new Promise((resolve, reject) => {
      if (window.Plaid) {
        resolve()
        return
      }
      existing.addEventListener('load', resolve, { once: true })
      existing.addEventListener('error', reject, { once: true })
    })
    return plaidScriptPromise
  }

  plaidScriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.dataset.plaidLink = 'true'
    script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
    script.async = true
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
  return plaidScriptPromise
}

/**
 * Launch the Plaid link flow for the selected product scopes.
 */
const linkPlaid = async () => {
  if (isDisabled.value) return

  errorMessage.value = ''
  statusMessage.value = 'Preparing secure Plaid connection…'
  loading.value = true

  try {
    try {
      await ensurePlaidScript()
    } catch (error) {
      publishLauncherError(
        'PLAID_SCRIPT_LOAD_FAILED',
        'Unable to load Plaid right now. Please refresh and try again.',
        error,
      )
      return
    }

    statusMessage.value = 'Generating a secure link token…'

    const payload = { products: props.selectedProducts }
    if (props.userId) {
      payload.user_id = props.userId
    }

    const { link_token, status, message } = await accountLinkApi.generateLinkToken(payload)

    if (status === 'error') {
      publishLauncherError(
        'LINK_TOKEN_GENERATION_FAILED',
        message || 'Unable to generate a link token. Please try again.',
        message,
      )
      return
    }

    if (!link_token || !window.Plaid) {
      publishLauncherError(
        'MISSING_LINK_TOKEN_OR_SDK',
        'We could not initialize Plaid. Please try again in a moment.',
      )
      return
    }

    statusMessage.value = 'Opening Plaid Link…'

    const handler = window.Plaid.create({
      token: link_token,
      onSuccess: async (public_token) => {
        const exchangePayload = { public_token, products: props.selectedProducts }
        if (props.userId) {
          exchangePayload.user_id = props.userId
        }

        statusMessage.value = 'Finalizing your linked account…'

        try {
          await accountLinkApi.exchangePublicToken(exchangePayload)
          statusMessage.value = ''
          emit('refresh')
        } catch (error) {
          publishLauncherError(
            'PUBLIC_TOKEN_EXCHANGE_FAILED',
            'We could not finish linking the account. Please retry.',
            error,
          )
        }
      },
      onExit: () => {
        console.log('Plaid flow exited')
        if (!errorMessage.value) {
          statusMessage.value = ''
        }
      },
    })

    handler.open()
  } catch (e) {
    publishLauncherError('PLAID_LINK_FLOW_FAILED', 'An unexpected error occurred while linking.', e)
  } finally {
    loading.value = false
  }
}
</script>
