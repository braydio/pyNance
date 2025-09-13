<!--
  PlanningSummary.vue
  -------------------
  Display a summary of total bills and remaining cash.
-->

<template>
  <div class="planning-summary">
    <h3>Planning Summary</h3>
    <p>Total Bills: {{ totalBills }}</p>
    <p>Remaining Cash: {{ remainingCash }}</p>
  </div>
</template>

<script setup>
/**
 * PlanningSummary component.
 *
 * Shows the total amount of all bills and the remaining unallocated
 * cash for the active scenario using shared planning state and
 * selectors.
 */
import { computed } from 'vue'
import { usePlanning } from '@/composables/usePlanning'
import {
  selectActiveScenario,
  selectRemainingCents,
  selectTotalBillsCents,
} from '@/selectors/planning'
import { formatAmount } from '@/utils/format'

/** Access reactive planning state. */
const { state } = usePlanning()

/**
 * Total amount across all bills formatted as currency.
 *
 * @returns {string} formatted total of all bills
 */
const totalBills = computed(() =>
  formatAmount(selectTotalBillsCents(state) / 100),
)

/**
 * Remaining unallocated cash for the active scenario formatted as
 * currency.
 *
 * @returns {string} formatted remaining cash
 */
const remainingCash = computed(() => {
  const scenario = selectActiveScenario(state)
  return formatAmount(selectRemainingCents(scenario) / 100)
})
</script>

<style scoped>
/* Basic styling placeholder for PlanningSummary */
</style>

