<template>
  <section class="summary-card" data-testid="planning-summary">
    <header class="flex flex-wrap items-start justify-between gap-2">
      <div>
        <h3 class="text-lg font-semibold">{{ scenarioName }}</h3>
        <p class="text-sm text-muted">Where your planning balance stands right now.</p>
      </div>
      <UiButton variant="outline" @click="emit('refresh')">Refresh</UiButton>
    </header>

    <p
      v-if="remainingCents < 0"
      class="summary-warning"
      role="alert"
      data-testid="over-allocated-warning"
    >
      Bills and allocations exceed your planning balance by {{ overAmountFormatted }}.
    </p>

    <dl class="summary-grid">
      <div class="summary-grid__lead">
        <dt>Planning balance</dt>
        <dd>{{ planningBalanceFormatted }}</dd>
      </div>
      <div>
        <dt>Listed plan bills</dt>
        <dd>{{ totalBillsFormatted }}</dd>
        <dd class="text-sm text-muted" data-testid="plan-bills-scope">
          This scenario only; mixed cadence, not a monthly total
        </dd>
      </div>
      <div>
        <dt>Allocated</dt>
        <dd>{{ allocatedFormatted }}</dd>
      </div>
      <div>
        <dt>Remaining</dt>
        <dd :class="{ 'text-error': remainingCents < 0 }">{{ remainingFormatted }}</dd>
      </div>
    </dl>

    <footer class="text-sm text-muted">Updated {{ lastSavedRelative }}</footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

const emit = defineEmits<{ (_e: 'refresh'): void }>()

const { state } = usePlanning()
const accountsById = ref<Record<string, { name?: string; institution_name?: string }>>({})

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
const overAmountFormatted = computed(() =>
  formatCurrency(Math.abs(Math.min(remainingCents.value, 0)) / 100, scenarioCurrency.value),
)
const planningBalanceFormatted = computed(() =>
  formatCurrency(planningBalanceCents.value / 100, scenarioCurrency.value),
)

const accountLabel = computed(() => {
  const accountId = activeScenario.value?.accountId
  if (!accountId) return ''
  const account = accountsById.value[accountId]
  if (!account) return ''
  if (account.name && account.institution_name) {
    return `${account.name} • ${account.institution_name}`
  }
  return account.name || account.institution_name || ''
})

const scenarioName = computed(() => {
  const scenario = activeScenario.value
  if (!scenario) return 'No scenario selected'
  if (accountLabel.value) {
    return `Plan for ${accountLabel.value}`
  }
  return scenario.name || 'No scenario selected'
})
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

/**
 * Fetch accounts so account-linked scenarios can display human-friendly labels.
 */
async function loadAccounts() {
  try {
    const response = await fetch('/api/accounts/get_accounts')
    const payload = await response.json()

    if (payload?.status === 'success' && Array.isArray(payload.accounts)) {
      accountsById.value = Object.fromEntries(
        payload.accounts.map((account: any) => [
          account.account_id,
          { name: account.name, institution_name: account.institution_name },
        ]),
      )
    }
  } catch (error) {
    console.error('Failed to load accounts for planning summary', error)
  }
}

onMounted(loadAccounts)
</script>

<style scoped>
.summary-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.5rem;
  border-radius: 0.75rem;
  border: 1px solid var(--border-subtle);
  background-color: var(--surface-1);
}

.summary-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.summary-grid dt {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.summary-grid dd {
  font-size: 1rem;
  font-weight: 600;
}

.summary-grid__lead dd {
  font-size: 1.75rem;
  font-weight: 700;
}

.summary-warning {
  color: var(--text-negative);
  font-size: 0.9375rem;
  font-weight: 600;
}

.text-muted {
  color: var(--text-muted);
}

.text-error {
  color: var(--text-negative);
}

.summary-grid dd {
  font-variant-numeric: tabular-nums;
}
</style>
