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
      Updated {{ lastSavedRelative }} · Planning account
      {{ planningAccountLabel || 'Unassigned' }}
    </footer>
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
import api from '@/services/api'
import { formatCurrency } from '@/utils/currency'

type AccountMetadata = {
  name?: string
  institution?: string
}

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
const accountLookup = ref<Record<string, AccountMetadata>>({})

const activeScenario = computed(() => {
  if (props.scenarioId) {
    return state.scenarios.find((scenario) => scenario.id === props.scenarioId)
  }
  return selectActiveScenario(state)
})

const planningAccountLabel = computed(() => {
  const accountId = activeScenario.value?.accountId
  if (!accountId) return ''
  const account = accountLookup.value[accountId]
  if (!account) return accountId

  const parts = [account.name, account.institution].filter(Boolean)
  return parts.length ? parts.join(' · ') : accountId
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

const scenarioName = computed(() => {
  const scenario = activeScenario.value
  if (!scenario) return 'No scenario selected'

  const defaultName = scenario.accountId ? `Plan for ${scenario.accountId}` : ''
  if (planningAccountLabel.value && (!scenario.name || scenario.name === defaultName)) {
    return `Plan for ${planningAccountLabel.value}`
  }

  return scenario.name || planningAccountLabel.value || 'No scenario selected'
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
 * Load account metadata to present a friendly planning account label.
 */
async function loadAccountMetadata() {
  try {
    const response = await api.getAccounts({ include_hidden: true })
    if (response?.status === 'success' && Array.isArray(response.accounts)) {
      const mapped = response.accounts.reduce<Record<string, AccountMetadata>>(
        (acc, account: any) => {
          const id = account.account_id ?? account.id
          if (!id) return acc
          acc[id] = {
            name: account.name,
            institution: account.institution_name,
          }
          return acc
        },
        {},
      )
      accountLookup.value = mapped
    }
  } catch (error) {
    console.error('Failed to load accounts for planning summary', error)
  }
}

onMounted(() => {
  loadAccountMetadata()
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
