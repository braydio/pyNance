<template>
  <div class="arbit-alerts">
    <div v-for="(alert, idx) in alerts" :key="idx" class="alert-item">
      Profit alert: {{ alert.net_profit_percent.toFixed(2) }}%
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * Notification center subscribing to Arbit profit alerts.
 */
import { ref, onMounted, onUnmounted } from 'vue'

const alerts = ref<Array<{ net_profit_percent: number; threshold: number }>>([])
let source: EventSource | null = null

onMounted(() => {
  source = new EventSource('/api/arbit/alerts/stream')
  source.onmessage = (event: MessageEvent) => {
    alerts.value.push(JSON.parse(event.data))
  }
})

onUnmounted(() => {
  source?.close()
})
</script>
