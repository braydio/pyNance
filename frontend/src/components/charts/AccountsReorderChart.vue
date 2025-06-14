<!--
  AccountsReorderChart.vue
  Displays top accounts split by assets and liabilities using gradient bars.
-->
<template>
  <div class="chart-container card">
    <h2 class="heading-md">Top {{ accountSubtype }} Accounts</h2>

    <div v-if="positiveAccounts.length" class="bar-chart">
      <h3 class="subheading">Assets</h3>
      <div v-for="account in positiveAccounts" :key="`p-${account.id}`" class="bar-row">
        <span class="bar-label">{{ account.name }} {{ format(account.adjusted_balance) }}</span>
        <div class="bar-outer">
          <div
            class="bar-fill"
            :class="barColor(account)"
            :style="{ width: barWidth(account) }"
          />
        </div>
      </div>
      <div class="axis">
        <div class="axis-line" />
        <span
          v-for="(tick, idx) in ticks"
          :key="idx"
          class="axis-tick"
          :style="{ left: `${(idx / (ticks.length - 1)) * 100}%` }"
        >
          {{ format(tick) }}
        </span>
      </div>
    </div>
    <div v-if="negativeAccounts.length" class="bar-chart">
      <h3 class="subheading">Liabilities</h3>
      <div v-for="account in negativeAccounts" :key="`n-${account.id}`" class="bar-row">
        <span class="bar-label">{{ account.name }} {{ format(account.adjusted_balance) }}</span>
        <div class="bar-outer">
          <div
            class="bar-fill"
            :class="barColor(account)"
            :style="{ width: barWidth(account) }"
          />
        </div>
      </div>
      <div class="axis">
        <div class="axis-line" />
        <span
          v-for="(tick, idx) in ticks"
          :key="idx"
          class="axis-tick"
          :style="{ left: `${(idx / (ticks.length - 1)) * 100}%` }"
        >
          {{ format(tick) }}
        </span>
      </div>
    </div>

    <div class="bar-axis" v-if="allVisibleAccounts.length">
      <span
        v-for="n in 5"
        :key="n"
        class="tick"
        :style="{ left: `${((n - 1) / 4) * 100}%` }"
      >
        {{ format(((n - 1) / 4) * maxValue) }}
      </span>
    </div>

    <p
      v-if="!positiveAccounts.length && !negativeAccounts.length"
      class="no-data-msg"
    >
      No accounts available for this subtype.
    </p>
  </div>
</template>

<script setup>
// Display top accounts grouped by subtype using simple bar charts.
// Bars use Tailwind colors with optional axis ticks for context.
import { toRef, onMounted, computed } from 'vue'
import { useTopAccounts } from '@/composables/useTopAccounts'

const props = defineProps({
  accountSubtype: {
    type: String,
    default: '',
  },
})

const format = val => new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
}).format(val)

const {
  positiveAccounts,
  negativeAccounts,
  allVisibleAccounts,
  fetchAccounts,
} = useTopAccounts(toRef(props, 'accountSubtype'))

onMounted(fetchAccounts)

const maxVal = computed(() =>
  Math.max(...allVisibleAccounts.value.map(a => Math.abs(a.adjusted_balance)), 1)
)

const ticks = computed(() => {
  const step = maxVal.value / 4
  return Array.from({ length: 5 }, (_, i) => i * step)
})

const barWidth = account => {
  return `${(Math.abs(account.adjusted_balance) / maxVal.value) * 100}%`
}

const barColor = account =>
  account.adjusted_balance >= 0 ? 'bg-blue-500' : 'bg-red-500'

defineExpose({
  refresh: fetchAccounts,
})
</script>


<style scoped>
.chart-container {
  padding: 1rem 1.25rem;
  background: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 1rem;
}

.bar-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.bar-label {
  flex: 1;
  font-weight: 500;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-outer {
  flex: 4;
  background: var(--color-bg-dark);
  border-radius: 6px;
  height: 14px;
  position: relative;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.6s ease-out;
  position: relative;
}

.axis {
  position: relative;
  height: 24px;
  margin-top: 0.5rem;
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.axis-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--color-border-secondary);
}

.axis-tick {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.axis-tick::before {
  content: '';
  width: 1px;
  height: 4px;
  background: var(--color-border-secondary);
  margin-bottom: 2px;
}



.subheading {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--color-text-muted);
  margin-bottom: 0.75rem;
}

.no-data-msg {
  text-align: center;
  font-style: italic;
  color: var(--color-text-muted);
  padding: 1rem 0.5rem;
}
</style>
