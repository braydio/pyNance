<!--
  AccountSparkline.vue
  Renders a simple SVG sparkline for an account's balance history.
-->
<template>
  <svg v-if="points" viewBox="0 0 100 100" class="bs-sparkline" role="img" :aria-label="ariaLabel">
    <polyline :points="points" />
  </svg>
  <span v-else class="bs-sparkline-placeholder" role="img" aria-label="No balance history available"></span>
</template>

<script setup>
import { computed, toRef } from 'vue'
import { useAccountHistory } from '@/composables/useAccountHistory'

const props = defineProps({
  accountId: { type: String, required: true }
})

const { history } = useAccountHistory(toRef(props, 'accountId'))

const ariaLabel = computed(() => `Recent balance history for account ${props.accountId}`)

const points = computed(() => {
  const data = history.value
  if (!data.length) return ''
  const max = Math.max(...data.map(d => d.balance))
  const min = Math.min(...data.map(d => d.balance))
  const range = max - min || 1
  const step = data.length > 1 ? data.length - 1 : 1
  return data
    .map((d, idx) => {
      const x = (idx / step) * 100
      const y = 100 - ((d.balance - min) / range) * 100
      return `${x},${y}`
    })
    .join(' ')
})
</script>

<style scoped>
.bs-sparkline {
  width: 60px;
  height: 20px;
  stroke: currentColor;
  fill: none;
  stroke-width: 1.5;
}

.bs-sparkline-placeholder {
  width: 60px;
  height: 20px;
}
</style>
