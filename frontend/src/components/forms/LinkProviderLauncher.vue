<template>
  <slot :linkPlaid="linkPlaid" :loading="loading" :isDisabled="isDisabled" />
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

const emit = defineEmits(['refresh'])

const loading = ref(false)
const isDisabled = computed(() => props.selectedProducts.length === 0 || loading.value)

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
  loading.value = true

  try {
    await ensurePlaidScript()

    const payload = { products: props.selectedProducts }
    if (props.userId) {
      payload.user_id = props.userId
    }

    const { link_token, status, message } = await accountLinkApi.generateLinkToken(payload)

    if (status === 'error') {
      console.error('Failed to generate link token:', message)
      return
    }

    if (!link_token || !window.Plaid) {
      console.error('Missing Plaid link token or SDK.')
      return
    }

    const handler = window.Plaid.create({
      token: link_token,
      onSuccess: async (public_token) => {
        const exchangePayload = { public_token, products: props.selectedProducts }
        if (props.userId) {
          exchangePayload.user_id = props.userId
        }
        await accountLinkApi.exchangePublicToken(exchangePayload)
        emit('refresh')
      },
      onExit: () => {
        console.log('Plaid flow exited')
      },
    })

    handler.open()
  } catch (e) {
    console.error('Error linking Plaid:', e)
  } finally {
    loading.value = false
  }
}
</script>
