<template>
  <div class="section-container mt-4">
    <h3 class="text-md font-medium mb-2">Link Provider</h3>

    <div class="flex gap-2">
      <button class="btn btn-pill" :class="{ 'opacity-50 cursor-not-allowed': selectedProducts.length === 0 }"
        :disabled="selectedProducts.length === 0 || loading" @click="linkPlaid">
        {{ loading && activeProvider === 'plaid' ? 'Linking...' : 'Link with Plaid' }}
      </button>

      <button class="btn btn-pill" :class="{ 'opacity-50 cursor-not-allowed': selectedProducts.length === 0 }"
        :disabled="selectedProducts.length === 0 || loading" @click="linkTeller">
        {{ loading && activeProvider === 'teller' ? 'Linking...' : 'Link with Teller.io' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
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
const activeProvider = ref(null)

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
  activeProvider.value = 'plaid'

  try {
    await ensurePlaidScript()

    const { link_token } = await accountLinkApi.generateLinkToken('plaid', {
      user_id: props.userId,
      products: props.selectedProducts,
    })

    if (!link_token || !window.Plaid) {
      console.error('Missing Plaid link token or SDK.')
      return
    }

    const handler = window.Plaid.create({
      token: link_token,
      onSuccess: async (public_token) => {
        await accountLinkApi.exchangePublicToken('plaid', {
          public_token,
          user_id: props.userId,
        })
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
    activeProvider.value = null
  }
}

const linkTeller = async () => {
  if (props.selectedProducts.length === 0) return
  loading.value = true
  activeProvider.value = 'teller'

  try {
    const connect = window.TellerConnect.setup({
      applicationId: import.meta.env.VITE_TELLER_APP_ID,
      environment: import.meta.env.VITE_TELLER_ENV || 'sandbox',
      products: props.selectedProducts,
      onSuccess: async (enrollment) => {
        await accountLinkApi.exchangePublicToken('teller', {
          public_token: enrollment.accessToken,
          user_id: props.userId,
        })
        emit('refresh')
      },
    })

    connect.open()
  } catch (e) {
    console.error('Error linking Teller:', e)
  } finally {
    loading.value = false
    activeProvider.value = null
  }
}
</script>
