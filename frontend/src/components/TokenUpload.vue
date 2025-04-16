
<template>
  <div class="max-w-xl mx-auto p-4 space-y-4">
    <h2 class="text-2xl font-semibold">📥 Import Plaid Accounts</h2>

    <div>
      <label class="block text-sm font-medium mb-1">User ID</label>
      <input v-model="userId" class="w-full border rounded px-3 py-2" placeholder="e.g. brayden123" />
    </div>

    <div>
      <label class="block text-sm font-medium mb-1">Access Token</label>
      <textarea
        v-model="accessToken"
        rows="4"
        class="w-full border rounded px-3 py-2"
        placeholder="Paste Plaid access token here..."
      ></textarea>
    </div>

    <button
      :disabled="loading || !userId || !accessToken"
      @click="submitToken"
      class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
    >
      🔄 Upload Accounts
    </button>

    <div v-if="result" class="mt-4 text-sm">
      <div v-if="result.success" class="text-green-600">
        ✅ Imported {{ result.count }} account(s) for {{ result.institution }}.
      </div>
      <div v-else class="text-red-600">
        ❌ {{ result.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const userId = ref('')
const accessToken = ref('')
const result = ref(null)
const loading = ref(false)

const submitToken = async () => {
  loading.value = true
  result.value = null
  try {
    const res = await axios.post('/api/plaid/accounts/import_manual', {
      user_id: userId.value,
      access_token: accessToken.value
    })
    result.value = res.data
  } catch (err) {
    result.value = {
      success: false,
      error: err.response?.data?.error || err.message
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
textarea {
  font-family: monospace;
}
</style>
