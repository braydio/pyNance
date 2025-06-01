<template>
  <div class="p-6 space-y-6">
    <!-- App Header -->
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-800">pyNance Dashboard</h1>
      <button
        @click="refreshData"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
      >
        Refresh
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Net Worth</p>
        <p class="text-xl font-semibold text-green-600">$24,893.22</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">YTD Spending</p>
        <p class="text-xl font-semibold text-red-500">$9,340.12</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Total Accounts</p>
        <p class="text-xl font-semibold text-gray-800">6</p>
      </div>
      <div class="bg-white shadow rounded-lg p-4">
        <p class="text-sm text-gray-500">Upcoming Bills</p>
        <p class="text-xl font-semibold text-yellow-600">$1,203.55</p>
      </div>
    </div>

    <!-- Remote Webhook Command Trigger -->
    <div class="bg-white shadow rounded p-6 space-y-4 max-w-md">
      <h2 class="text-lg font-bold text-gray-800">Remote Command Trigger</h2>

      <input
        v-model="payload.command"
        placeholder="Enter command"
        class="w-full border px-3 py-2 rounded text-sm"
      />

      <button
        @click="sendCommand"
        :disabled="loading"
        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
      >
        {{ loading ? 'Sending...' : 'Send Command' }}
      </button>

      <p v-if="response" class="text-sm mt-2 text-green-700">
        ✅ {{ response }}
      </p>
      <p v-if="error" class="text-sm mt-2 text-red-600">
        ⚠️ {{ error }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const payload = ref({ command: '' })
const loading = ref(false)
const response = ref(null)
const error = ref(null)

const WEBHOOK_URL = 'https://your-remote-url/api/webhook' // Replace with your actual endpoint

async function sendCommand() {
  loading.value = true
  response.value = null
  error.value = null

  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload.value),
    })

    if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`)

    const data = await res.json()
    response.value = data.message || 'Command sent successfully.'
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function refreshData() {
  // Placeholder for actual refresh logic
  console.log("Refreshing data...")
}
</script>