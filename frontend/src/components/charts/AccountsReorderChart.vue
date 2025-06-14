<!--
  AccountsReorderChart.vue
  Displays top accounts split by assets and liabilities using gradient bars.
-->
<template>
  <div class="chart-container card">
    <h2 class="heading-md">Top {{ accountSubtype }} Accounts</h2>

    <div v-if="positiveAccounts.length" class="bar-chart">
      <h3 class="subheading">Assets</h3>
      <div
        v-for="account in positiveAccounts"
        :key="`p-${account.id}`"
        class="bar-row"
        :title="`${account.name}: ${format(account.adjusted_balance)}`"
      >
        <span class="bar-label">{{ account.name }}</span>
        <span class="label-balance">{{ format(account.adjusted_balance) }}</span>
        <div class="bar-outer">
          <div class="bar-fill asset-fill" :style="{ width: barWidth(account) }">
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="negativeAccounts.length" class="bar-chart">
      <h3 class="subheading">Liabilities</h3>
      <div
        v-for="account in negativeAccounts"
        :key="`n-${account.id}`"
        class="bar-row"
        :title="`${account.name}: ${format(account.adjusted_balance)}`"
      >
        <span class="bar-label">{{ account.name }}</span>
        <span class="label-balance">{{ format(account.adjusted_balance) }}</span>
        <div class="bar-outer">
          <div class="bar-fill liability-fill" :style="{ width: barWidth(account) }">
            <span class="bar-value">{{ format(account.adjusted_balance) }}</span>
          </div>
        </div>
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

const { positiveAccounts, negativeAccounts, allVisibleAccounts, fetchAccounts } =
  useTopAccounts(toRef(props, 'accountSubtype'))

onMounted(fetchAccounts)

const maxValue = computed(() =>
  Math.max(
    ...allVisibleAccounts.value.map(a => Math.abs(a.adjusted_balance)),
    1
  )
)

const barWidth = account => `${(Math.abs(account.adjusted_balance) / maxValue.value) * 100}%`

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

.asset-fill {
  background: linear-gradient(
    to right,
    var(--asset-gradient-start),
    var(--asset-gradient-end)
  );
}

.liability-fill {
  background: linear-gradient(
    to right,
    var(--liability-gradient-start),
    var(--liability-gradient-end)
  );
}

.bar-value {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
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
