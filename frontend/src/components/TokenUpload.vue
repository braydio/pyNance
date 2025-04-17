
<template>
  <div class="link-account">
    <h2>Link Account (Manual)</h2>
    <div class="button-group">
      <button @click="showForm = !showForm" class="btn">
        {{ showForm ? 'Hide Form' : '+ Paste Access Token' }}
      </button>
    </div>

    <transition name="fade">
      <div v-if="showForm" class="upload-form">
        <div class="mb-2">
          <label class="text-xs font-medium">User ID</label>
          <input
            v-model="userId"
            class="w-full px-2 py-1 border rounded text-sm"
            placeholder="e.g. brayden"
          />
        </div>

        <div class="mb-2">
          <label class="text-xs font-medium">Access Token</label>
          <textarea
            v-model="accessToken"
            class="w-full px-2 py-1 border rounded text-sm"
            rows="2"
            placeholder="Paste access token"
          ></textarea>
        </div>

        <div class="button-group justify-between">
          <button
            @click="submit"
            :disabled="!userId || !accessToken || loading"
            class="btn"
          >
            Upload
          </button>
          <button class="btn" @click="showForm = false">Cancel</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const showForm = ref(false)
const userId = ref('')
const accessToken = ref('')
const loading = ref(false)

const submit = async () => {
  loading.value = true
  try {
    await axios.post('/api/plaid/accounts/import_manual', {
      user_id: userId.value,
      access_token: accessToken.value
    })
    showForm.value = false
    userId.value = ''
    accessToken.value = ''
  } catch (e) {
    alert(e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.link-account {
  margin: 0 auto;
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border-top: 8px inset var(--color-bg-secondary);
  border-bottom: 6px outset var(--color-text-muted);
  border-left: 8px inset var(--color-bg-secondary);
  border-right: 6px outset var(--color-text-muted);
  border-radius: 5px;
}
.link-account h2 {
  margin: 5px 1px;
  color: var(--neon-purple);
  text-align: center;
}
.button-group {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
}
.button-group button {
  background-color: var(--themed-bg);
  color: var(--color-text-light);
  border: 1px groove transparent;
  border-radius: 3px;
  font-weight: bold;
  cursor: pointer;
}
.button-group button:hover {
  color: var(--themed-bg);
  background-color: var(--neon-mint);
}
.upload-form {
  margin-top: 1rem;
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  border: 1px solid var(--divider);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
  width: 100%;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}
</style>

