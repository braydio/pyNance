<template>
  <div class="arbit-logs" data-testid="arbit-logs">
    <div class="logs-header">
      <div class="badge-row">
        <span class="live-pill">Live</span>
        <p class="helper-text">Latest RSAssistant activity</p>
      </div>
      <p class="timestamp" data-testid="last-updated">Updated {{ lastUpdatedLabel }}</p>
    </div>

    <div class="log-surface" role="log" aria-live="polite">
      <div v-if="errorMessage" class="log-placeholder error">{{ errorMessage }}</div>
      <div v-else-if="loading" class="log-placeholder">Loading logs...</div>
      <div v-else-if="!logs.length" class="log-placeholder">No log entries available.</div>
      <ul v-else class="log-list">
        <li v-for="(entry, index) in logs" :key="`${index}-${entry}`" class="log-line">
          {{ entry }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Live feed of RSAssistant log output for the Arbit dashboard.
 */
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { fetchArbitLogs, type ArbitLogResponse } from '@/services/arbit'

const logs = ref<string[]>([])
const loading = ref(true)
const errorMessage = ref('')
const lastUpdated = ref<string | null>(null)
let intervalId: number | undefined

const lastUpdatedLabel = computed(() => {
  if (!lastUpdated.value) return 'awaiting first update'
  const parsed = new Date(lastUpdated.value)
  if (Number.isNaN(parsed.getTime())) return 'unavailable'
  return parsed.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
})

const loadLogs = async () => {
  try {
    const data: ArbitLogResponse = await fetchArbitLogs()
    logs.value = data.lines ?? []
    lastUpdated.value = data.last_updated ?? null
    errorMessage.value = ''
  } catch (err) {
    console.error('Failed to load RSAssistant logs', err)
    errorMessage.value = 'Unable to load logs right now.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
  intervalId = window.setInterval(loadLogs, 5000)
})

onUnmounted(() => {
  if (intervalId) {
    window.clearInterval(intervalId)
  }
})
</script>

<style scoped>
@reference "../assets/css/main.css";

.arbit-logs {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.logs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.badge-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  font-weight: 700;
  color: var(--color-bg-dark);
  background: linear-gradient(135deg, var(--color-accent-cyan), var(--color-accent-blue));
  box-shadow: 0 8px 20px rgba(99, 205, 207, 0.25);
}

.helper-text {
  margin: 0;
  color: var(--color-text-muted);
}

.timestamp {
  margin: 0;
  color: var(--color-accent-cyan);
  font-weight: 600;
}

.log-surface {
  background: var(--themed-bg);
  border: 1px solid var(--divider);
  border-radius: 0.75rem;
  padding: 0.75rem;
  min-height: 200px;
  max-height: 360px;
  overflow-y: auto;
  box-shadow: var(--shadow);
}

.log-placeholder {
  color: var(--color-text-muted);
  text-align: center;
  padding: 1rem 0.5rem;
}

.log-placeholder.error {
  color: var(--color-accent-red);
}

.log-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.log-line {
  padding: 0.35rem 0.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 0.5rem;
  border: 1px solid transparent;
  color: var(--theme-fg);
  font-family: var(--font-sans);
  font-size: 0.95rem;
  letter-spacing: -0.01em;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.log-line:hover {
  background: rgba(99, 205, 207, 0.08);
  border-color: var(--divider);
}
</style>
