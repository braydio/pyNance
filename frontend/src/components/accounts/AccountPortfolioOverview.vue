<!--
  AccountPortfolioOverview.vue
  All-accounts summary: assets, liabilities, net position, credit utilization, and type chips.
  Consumes the parent-owned `accounts` list only (no fetching).
-->
<template>
  <section
    class="portfolio-overview"
    aria-labelledby="portfolio-overview-title"
    data-testid="portfolio-overview"
  >
    <h2 id="portfolio-overview-title" class="sr-only">Accounts overview</h2>

    <p
      v-if="totals.mixedCurrency"
      class="portfolio-note"
      role="status"
      data-testid="mixed-currency-note"
    >
      Accounts use more than one currency, so combined totals are not shown.
    </p>

    <dl class="portfolio-kpis">
      <div class="portfolio-kpi" data-testid="kpi-assets">
        <dt>Assets</dt>
        <dd>{{ money(totals.assets) }}</dd>
      </div>
      <div class="portfolio-kpi" data-testid="kpi-liabilities">
        <dt>Liabilities</dt>
        <dd :class="amountPolarityClass(totals.liabilities ? -totals.liabilities : 0)">
          {{ money(totals.liabilities) }}
        </dd>
      </div>
      <div class="portfolio-kpi portfolio-kpi--primary" data-testid="kpi-net">
        <dt>{{ netLabel }}</dt>
        <dd :class="amountPolarityClass(totals.net)">{{ money(totals.net) }}</dd>
      </div>
      <div class="portfolio-kpi" data-testid="kpi-utilization">
        <dt>Credit utilization</dt>
        <dd>{{ utilizationLabel }}</dd>
        <dd class="portfolio-kpi__sub" data-testid="utilization-coverage">{{ coverageLabel }}</dd>
      </div>
    </dl>

    <p class="portfolio-note" data-testid="scope-line">{{ scopeLine }}</p>
    <p v-if="totals.hiddenIncluded" class="portfolio-note" data-testid="hidden-included-note">
      Totals include hidden accounts.
    </p>
    <p
      v-else-if="totals.hiddenCount"
      class="portfolio-note portfolio-note--caution"
      data-testid="hidden-excluded-note"
    >
      {{ totals.hiddenCount }} hidden
      {{ totals.hiddenCount === 1 ? 'account is' : 'accounts are' }} not included, so these totals
      are a partial picture.
    </p>
    <p
      v-if="totals.unknownBalances"
      class="portfolio-note portfolio-note--caution"
      data-testid="unknown-balances-note"
    >
      {{ totals.unknownBalances }}
      {{ totals.unknownBalances === 1 ? 'account has' : 'accounts have' }} no balance data and
      {{ totals.unknownBalances === 1 ? 'is' : 'are' }} not counted as $0.
    </p>

    <div class="portfolio-chips" role="group" aria-label="Filter by account type">
      <button
        v-for="chip in chips"
        :key="chip.value"
        type="button"
        class="portfolio-chip"
        :class="{ 'portfolio-chip--active': chip.value === group }"
        :aria-pressed="chip.value === group"
        :data-testid="`type-chip-${chip.value}`"
        @click="emit('update:group', chip.value)"
      >
        <span class="portfolio-chip__label">{{ chip.label }}</span>
        <span class="portfolio-chip__count">{{ chip.count }}</span>
        <span v-if="chip.amount" class="portfolio-chip__amount">{{ chip.amount }}</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { amountPolarityClass, formatAmount } from '@/utils/format'
import { GROUPS, GROUP_LABELS, isLiabilityGroup, portfolioTotals } from '@/utils/accountPortfolio'

const props = defineProps({
  accounts: { type: Array, default: () => [] },
  group: { type: String, default: 'all' },
  includeHidden: { type: Boolean, default: false },
})
const emit = defineEmits(['update:group'])

const totals = computed(() =>
  portfolioTotals(props.accounts, { includeHidden: props.includeHidden }),
)

function money(value) {
  return value === null || value === undefined ? 'Unavailable' : formatAmount(value)
}

const utilizationLabel = computed(() => {
  const { percent } = totals.value.utilization
  return percent === null ? 'N/A' : `${percent}%`
})

const coverageLabel = computed(() => {
  const { known, total } = totals.value.utilization
  if (!total) return 'No credit cards'
  return `Known credit limits: ${known}/${total} ${total === 1 ? 'card' : 'cards'}`
})

/** Net is only an unqualified total when nothing is left out. */
const netLabel = computed(() => (totals.value.partial ? 'Visible-account net' : 'Net position'))

const scopeLine = computed(() => {
  const { accountCount, linkedCount, hiddenCount, hiddenIncluded } = totals.value
  if (hiddenIncluded || !hiddenCount) {
    return `${accountCount} of ${linkedCount} linked ${linkedCount === 1 ? 'account' : 'accounts'} included`
  }
  return `${accountCount} visible of ${linkedCount} linked; ${hiddenCount} hidden excluded`
})

const chips = computed(() => {
  const all = {
    value: 'all',
    label: 'All',
    count: totals.value.accountCount,
    amount: '',
  }
  const groups = GROUPS.map((group) => {
    const bucket = totals.value.groups[group]
    let amount = ''
    if (bucket.count && !totals.value.mixedCurrency) {
      amount = isLiabilityGroup(group)
        ? `${formatAmount(bucket.total)} owed`
        : formatAmount(bucket.total)
    }
    return { value: group, label: GROUP_LABELS[group], count: bucket.count, amount }
  }).filter((chip) => chip.count > 0)
  return [all, ...groups]
})
</script>

<style scoped>
.portfolio-overview {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* KPI tiles share the card's surface instead of boxing each number again. */
.portfolio-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 11rem), 1fr));
  gap: 0.75rem;
  margin: 0;
}

.portfolio-kpi {
  padding: 0.7rem 0.9rem;
  border-radius: 0.6rem;
  background: var(--surface-1);
}

.portfolio-kpi dt {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.portfolio-kpi dd {
  margin: 0.15rem 0 0;
  font-size: 1.25rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

/* Net position is the headline: larger, with an accent edge. */
.portfolio-kpi--primary {
  background: var(--surface-2);
  border-left: 4px solid var(--color-accent-cyan);
}

.portfolio-kpi--primary dd {
  font-size: 1.5rem;
}

.portfolio-kpi dd.portfolio-kpi__sub {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.portfolio-note {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

/* A partial picture is a real caution: amber edge and readable text on any theme. */
.portfolio-note--caution {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  color: var(--color-text-light, inherit);
  background: color-mix(in srgb, var(--color-warning) 12%, var(--surface-1));
  border-left: 4px solid color-mix(in srgb, var(--color-warning) 70%, transparent);
}

.portfolio-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.portfolio-chip {
  display: inline-flex;
  flex-wrap: wrap;
  max-width: 100%;
  align-items: baseline;
  gap: 0.15rem 0.4rem;
  text-align: left;
  padding: 0.3rem 0.7rem;
  border: 1px solid var(--themed-border);
  border-radius: 9999px;
  background: transparent;
  color: inherit;
  font-size: 0.875rem;
  cursor: pointer;
}

.portfolio-chip:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

.portfolio-chip--active {
  border-color: var(--color-accent-cyan);
  background: color-mix(in srgb, var(--color-accent-cyan) 14%, transparent);
}

.portfolio-chip__count {
  font-weight: 700;
}

.portfolio-chip__amount {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}
</style>
