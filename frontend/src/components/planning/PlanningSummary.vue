<template>
  <section class="summary-card" data-testid="planning-summary">
    <header class="flex items-start justify-between">
      <div>
        <h3 class="text-lg font-semibold">{{ scenarioName }}</h3>
        <p class="text-sm text-muted">Snapshot of bills and allocations for this scenario.</p>
      </div>
      <UiButton variant="outline" @click="emit('refresh')">Refresh</UiButton>
    </header>

    <dl class="summary-grid">
      <div>
        <dt>Total planned bills</dt>
        <dd>{{ totalBillsFormatted }}</dd>
      </div>
      <div>
        <dt>Planning balance</dt>
        <dd>{{ planningBalanceFormatted }}</dd>
      </div>
      <div>
        <dt>Allocated so far</dt>
        <dd>{{ allocatedFormatted }}</dd>
      </div>
      <div>
        <dt>Remaining cash</dt>
        <dd :class="{ 'text-error': remainingCents < 0 }">{{ remainingFormatted }}</dd>
      </div>
    </dl>

    <footer class="text-xs text-muted">
      Updated {{ lastSavedRelative }} · Scenario ID {{ activeScenario?.id ?? 'n/a' }}
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UiButton from '@/components/ui/Button.vue'
import { usePlanning } from '@/composables/usePlanning'
import {
  selectActiveScenario,
  selectAllocatedCents,
  selectRemainingCents,
  selectTotalBillsCents,
} from '@/selectors/planning'
import { formatCurrency } from '@/utils/currency'

const props = withDefaults(
  defineProps<{
    scenarioId?: string
    currencyCode?: string
  }>(),
  {
    currencyCode: undefined,
  },
)

const emit = defineEmits<{ (e: 'refresh'): void }>()

const { state } = usePlanning()

const activeScenario = computed(() => {
  if (props.scenarioId) {
    return state.scenarios.find((scenario) => scenario.id === props.scenarioId)
  }
  return selectActiveScenario(state)
})

const scenarioCurrency = computed(
  () => props.currencyCode ?? activeScenario.value?.currencyCode ?? 'USD',
)

const totalBillsCents = computed(() => selectTotalBillsCents(state, activeScenario.value?.id))
const allocatedCents = computed(() => selectAllocatedCents(activeScenario.value ?? undefined))
const remainingCents = computed(() =>
  activeScenario.value ? selectRemainingCents(activeScenario.value) : 0,
)
const planningBalanceCents = computed(() => activeScenario.value?.planningBalanceCents ?? 0)

const totalBillsFormatted = computed(() =>
  formatCurrency(totalBillsCents.value / 100, scenarioCurrency.value),
)
const allocatedFormatted = computed(() =>
  formatCurrency(allocatedCents.value / 100, scenarioCurrency.value),
)
const remainingFormatted = computed(() =>
  formatCurrency(remainingCents.value / 100, scenarioCurrency.value),
)
const planningBalanceFormatted = computed(() =>
  formatCurrency(planningBalanceCents.value / 100, scenarioCurrency.value),
)

const scenarioName = computed(() => activeScenario.value?.name ?? 'No scenario selected')
const lastSavedRelative = computed(() => {
  if (!state.lastSavedAt) return 'just now'
  const saved = new Date(state.lastSavedAt)
  if (Number.isNaN(saved.getTime())) return 'recently'
  const now = new Date()
  const diffMinutes = Math.round((now.getTime() - saved.getTime()) / 60000)
  if (diffMinutes <= 1) return 'just now'
  if (diffMinutes < 60) return `${diffMinutes} minutes ago`
  const diffHours = Math.round(diffMinutes / 60)
  if (diffHours < 24) return `${diffHours} hours ago`
  const diffDays = Math.round(diffHours / 24)
  return `${diffDays} days ago`
})
</script>

<style scoped>
.summary-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background-color: var(--color-surface, #fff);
}

.summary-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.summary-grid dt {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-muted, #64748b);
}

.summary-grid dd {
  font-size: 1rem;
  font-weight: 600;
}

.text-muted {
  color: var(--color-muted, #64748b);
}

.text-error {
  color: #b91c1c;
}
</style>
