<template>
  <div class="section-container mt-4">
    <h3 class="text-md font-medium mb-2">Link accounts with Plaid</h3>

    <p class="text-sm text-neutral-400 mb-3">
      Select at least one product to enable the Plaid Link flow.
    </p>

    <div class="flex gap-2">
      <UiButton
        variant="primary"
        pill
        :class="{ 'opacity-50 cursor-not-allowed': selectedProducts.length === 0 }"
        :disabled="selectedProducts.length === 0 || loading"
        @click="linkPlaid"
      >
        {{ loading ? 'Linking…' : 'Link with Plaid' }}
      </UiButton>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UiButton from '@/components/ui/Button.vue'
import accountLinkApi from '@/api/accounts_link'

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

async function ensurePlaidScript() {
  if (window.Plaid) return

  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdn.plaid.com/link/v2/stable/link-initialize.js'
    script.async = true
    script.onload = resolve
    script.onerror = reject
    document.head.appendChild(script)
  })
}

const linkPlaid = async () => {
  if (props.selectedProducts.length === 0) return
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
