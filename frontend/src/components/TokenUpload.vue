
<template>
  <div class="relative">
    <button
      class="btn btn-outline btn-pill"
      @click="showForm = !showForm"
      type="button"
    >
      + Token Upload
    </button>

    <transition name="fade">
      <div
        v-if="showForm"
        class="absolute z-10 mt-2 p-4 rounded bg-white shadow-xl border border-gray-300 w-80"
      >
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
        <div class="flex justify-between items-center">
          <button
            @click="submit"
            :disabled="!userId || !accessToken || loading"
            class="btn btn-sm bg-blue-600 text-white hover:bg-blue-700 px-3 py-1 rounded"
          >
            Upload
          </button>
          <button class="text-xs text-gray-500" @click="showForm = false">
            Cancel
          </button>
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
textarea {
  font-family:"Fira Code" monospace;
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
