<!--
  TransactionInsightsPanel.vue
  Summary metrics and a short, prioritized review queue for the Transactions page. The numbers come
  from the server over ALL matching transactions in the period, not the rows loaded in the table.
  Cards only apply a filter or open a review tab: nothing here edits a transaction.
-->
<template>
  <section class="insights" aria-labelledby="insights-title" data-testid="insights-panel">
    <div class="insights__header">
      <div>
        <h2 id="insights-title" class="insights__title">Spending &amp; review</h2>
        <p class="insights__scope text-muted" data-testid="insights-scope">{{ scopeLabel }}</p>
      </div>
      <button
        type="button"
        class="btn btn-outline"
        data-testid="insights-refresh"
        :disabled="loading"
        @click="emit('refresh')"
      >
        {{ loading ? 'Updating...' : 'Update' }}
      </button>
    </div>

    <p v-if="error" class="text-negative" role="alert" data-testid="insights-error">
      {{ error }}
      <button type="button" class="btn-link" @click="emit('refresh')">Retry</button>
    </p>
    <p v-else-if="loading && !insights" class="text-muted" role="status">Loading summary...</p>

    <template v-if="insights">
      <dl class="insights__metrics">
        <div class="insights__metric" data-testid="metric-spending">
          <dt>Spending</dt>
          <dd>{{ money(insights.net_spend) }}</dd>
          <dd class="insights__sub">
            {{ money(insights.gross_spend) }} spent, {{ money(insights.refunds) }} refunded
          </dd>
        </div>
        <div class="insights__metric" data-testid="metric-income">
          <dt>Income</dt>
          <dd>{{ money(insights.income) }}</dd>
          <dd class="insights__sub" data-testid="income-explainer">
            Earned income only. Other credits: {{ money(otherCredits) }} (transfers
            {{ money(insights.inflow?.transfers_in) }}, unreviewed
            {{ money(insights.inflow?.unclassified_in) }})
          </dd>
        </div>
        <div class="insights__metric" data-testid="metric-review">
          <dt>Needs review</dt>
          <dd>{{ reviewCount }}</dd>
          <dd class="insights__sub">
            {{ insights.coverage?.unclassified_count ?? 0 }} unclassified ·
            {{ insights.uncategorized_count }} uncategorized
          </dd>
        </div>
        <div class="insights__metric" data-testid="metric-recurring">
          <dt>Recurring candidates</dt>
          <dd>{{ insights.recurring_candidate_count }}</dd>
          <dd class="insights__sub">{{ insights.transfer_pair_count }} possible transfer pairs</dd>
        </div>
      </dl>

      <p class="insights__count text-muted" data-testid="insights-matching">
        {{ Number(insights.matching_count).toLocaleString() }} matching transactions in this period
        (pending excluded)
      </p>

      <div v-if="insights.review_items?.length" data-testid="review-queue">
        <h3 class="insights__queue-title">Review queue</h3>
        <ul class="insights__queue">
          <li
            v-for="item in insights.review_items"
            :key="item.id"
            class="insights__item"
            :data-testid="`review-${item.kind}`"
          >
            <div class="insights__item-main">
              <p class="insights__item-text">{{ item.explanation }}</p>
              <p class="text-muted insights__item-evidence">
                {{ item.count }} {{ item.count === 1 ? 'transaction' : 'transactions' }} ·
                {{ money(item.amount_total) }} · {{ item.evidence.join(' · ') }}
              </p>
            </div>
            <button
              type="button"
              class="btn btn-outline"
              :aria-label="`${actionLabel(item)}: ${item.explanation}`"
              @click="emit('apply', item)"
            >
              {{ actionLabel(item) }}
            </button>
          </li>
        </ul>
      </div>
      <p v-else-if="!loading" class="text-muted" data-testid="review-empty">
        Nothing needs review in this period.
      </p>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  insights: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  /** Plain-language scope shown above the numbers, for example "Last 30 days". */
  scopeLabel: { type: String, default: '' },
})
const emit = defineEmits(['apply', 'refresh'])

function money(value) {
  return formatAmount(Number(value ?? 0))
}

const otherCredits = computed(() => {
  const inflow = props.insights?.inflow
  if (!inflow) return 0
  return Math.max(0, Number(inflow.all_credit_movements) - Number(inflow.economic_income))
})

const reviewCount = computed(() =>
  (props.insights?.review_items ?? []).reduce((total, item) => total + Number(item.count || 0), 0),
)

const ACTIONS = {
  transfer_candidate: 'Open Transfer Review',
  possible_duplicate_same_merchant_amount_day: 'Show these charges',
  bank_fee: 'Show fees',
  missing_category: 'Show uncategorized',
}

function actionLabel(item) {
  return ACTIONS[item.kind] || 'Show transactions'
}
</script>

<style scoped>
.insights {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.insights__header {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: space-between;
  align-items: flex-start;
}

.insights__title {
  font-size: 1.25rem;
  font-weight: 700;
}

.insights__scope {
  font-size: 0.875rem;
}

.insights__metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr));
  gap: 0.75rem;
  margin: 0;
}

.insights__metric {
  padding: 0.7rem 0.9rem;
  border-radius: 0.6rem;
  background: var(--surface-1);
}

.insights__metric dt {
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.insights__metric dd {
  margin: 0.1rem 0 0;
  font-size: 1.35rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.insights__metric dd.insights__sub {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.insights__count {
  font-size: 0.875rem;
  margin: 0;
}

.insights__queue-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.insights__queue {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.5rem;
}

.insights__item {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1rem;
  justify-content: space-between;
  align-items: center;
  padding: 0.65rem 0.9rem;
  border-radius: 0.6rem;
  background: var(--surface-1);
  border-left: 4px solid color-mix(in srgb, var(--color-warning) 65%, transparent);
}

.insights__item-main {
  min-width: 0;
  flex: 1 1 18rem;
}

.insights__item-text {
  margin: 0;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.insights__item-evidence {
  margin: 0.1rem 0 0;
  font-size: 0.875rem;
}

.btn-link {
  background: transparent;
  border: none;
  padding: 0 0.4rem;
  color: var(--text-link);
  cursor: pointer;
  text-decoration: underline;
}
</style>
