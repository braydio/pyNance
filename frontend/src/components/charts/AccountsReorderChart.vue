<template>
  <div class="chart-container card">
    <h2 class="heading-md">Top {{ accountSubtype }} Accounts</h2>

    <div v-if="positiveAccounts.length" class="bar-chart">
      <h3 class="subheading">Assets</h3>
      <div v-for="account in positiveAccounts" :key="`p-${account.id}`" class="bar-row">
        <span class="bar-label">{{ account.name }}</span>
        <div class="bar-outer">
          <div class="bar-fill bar-fill-asset" :style="{ width: barWidth(account) }">
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="negativeAccounts.length" class="bar-chart">
      <h3 class="subheading">Liabilities</h3>
      <div v-for="account in negativeAccounts" :key="`n-${account.id}`" class="bar-row">
        <span class="bar-label">{{ account.name }}</span>
        <div class="bar-outer">
          <div class="bar-fill bar-fill-liability" :style="{ width: barWidth(account) }">
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <p v-if="!positiveAccounts.length && !negativeAccounts.length" class="no-data-msg">
      No accounts available for this subtype.
    </p>
  </div>
</template>

<script setup>
import { toRef, onMounted } from 'vue'
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

const { positiveAccounts, negativeAccounts, allVisibleAccounts, fetchAccounts } =
  useTopAccounts(toRef(props, 'accountSubtype'))

onMounted(fetchAccounts)

const barWidth = account => {
  const max = Math.max(
    ...allVisibleAccounts.value.map(a => Math.abs(a.adjusted_balance)),
    1
  )
  return `${(Math.abs(account.adjusted_balance) / max) * 100}%`
}

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

.bar-fill-asset {
  background: linear-gradient(
    to right,
    var(--asset-gradient-start),
    var(--asset-gradient-end)
  );
}

.bar-fill-liability {
  background: linear-gradient(
    to right,
    var(--liability-gradient-start),
    var(--liability-gradient-end)
  );
}

.bar-value {
  position: absolute;
  right: 0.5rem;
  top: -1.5rem;
  font-size: 0.8rem;
  color: #ccd;
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
