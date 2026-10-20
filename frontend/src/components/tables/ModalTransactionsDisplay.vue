<template>
  <div class="ledger text-[var(--color-text-light)]">
    <div v-if="titleDate" class="px-3 pt-3 text-base font-medium">
      {{ titleDate }}
    </div>
    <div class="ledger-scroll">
      <table class="ledger-table">
        <caption class="ledger-caption--sr">
          {{
            titleDate ? `Transactions for ${titleDate}` : 'Transactions'
          }}
          ({{
            transactions.length
          }}
          shown)
        </caption>
        <thead>
          <tr>
            <th scope="col">Account</th>
            <th scope="col">{{ detailsHeader }}</th>
            <th scope="col" class="ledger-num">Amount</th>
            <th v-if="showDateColumn" scope="col" class="ledger-num">Date</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="tx in transactions"
            :key="tx.transaction_id"
            class="group ledger-row--clickable"
            tabindex="0"
            @click="$emit('row-click', tx)"
            @keydown.enter.prevent="$emit('row-click', tx)"
            @keydown.space.prevent="$emit('row-click', tx)"
          >
            <td class="min-w-[160px]">
              <div class="flex items-center gap-2">
                <img
                  v-if="tx.institution_icon_url"
                  :src="tx.institution_icon_url"
                  alt="Institution logo"
                  class="h-6 w-6 rounded-full object-contain"
                />
                <span
                  v-else
                  class="h-6 w-6 rounded-full bg-[var(--color-accent-purple)] flex items-center justify-center text-xs font-semibold text-[var(--color-text-dark)]"
                >
                  {{ initials(tx.institution_name) }}
                </span>
                <div class="flex flex-col">
                  <div class="font-medium">{{ tx.account_name }}</div>
                  <div class="ledger-secondary">{{ tx.institution_name }}</div>
                </div>
              </div>
            </td>
            <td>
              <div class="flex items-start gap-2">
                <img
                  v-if="showCategoryVisuals && tx.category_icon_url"
                  :src="tx.category_icon_url"
                  alt="Category icon"
                  class="h-6 w-6 object-contain flex-shrink-0"
                />
                <div class="flex flex-col flex-1 min-w-0">
                  <div class="font-medium truncate">{{ rowPrimaryLabel(tx) }}</div>
                  <div class="ledger-secondary truncate">
                    {{ rowSecondaryLabel(tx) }}
                  </div>
                  <span
                    v-if="flowChipLabel(tx)"
                    class="mt-1 inline-flex w-fit items-center rounded border border-[var(--color-text-muted)]/50 px-1.5 text-[0.65rem] font-semibold uppercase tracking-wide text-[var(--color-text-muted)]"
                    data-testid="flow-chip"
                    :title="flowTitle(tx)"
                    :aria-label="flowTitle(tx)"
                    >{{ flowChipLabel(tx) }}</span
                  >
                  <div
                    v-if="showCategoryVisuals && getCategoryDisplayName(tx)"
                    class="ledger-secondary italic mt-1"
                  >
                    {{ getCategoryDisplayName(tx) }}
                  </div>
                </div>
              </div>
            </td>
            <td class="ledger-num">
              <span :class="['font-semibold', amountClass(tx)]">
                {{ formatAmount(tx.amount) }}
              </span>
            </td>
            <td v-if="showDateColumn" class="ledger-num ledger-secondary">
              {{ formatDate(tx.date || tx.transaction_date) }}
            </td>
          </tr>
          <tr v-if="!transactions.length">
            <td :colspan="showDateColumn ? 4 : 3" class="ledger-state italic">
              No transactions found.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { formatAmount as utilFormatAmount } from '../../utils/format'
import { flowChipLabel, flowTitle, hasFlowKind } from '../../utils/flowSummary'

const props = defineProps({
  transactions: { type: Array, default: () => [] },
  titleDate: { type: String, default: '' },
  showDateColumn: { type: Boolean, default: false },
  showCategoryVisuals: { type: Boolean, default: true },
  detailsHeader: { type: String, default: 'Merchant' },
  primaryField: { type: String, default: 'merchant_name' }, // merchant_name | description
})

/**
 * Format a numeric amount using shared currency helpers.
 */
function formatAmount(amount) {
  if (amount == null) return '-'
  return utilFormatAmount(amount)
}
const ECONOMIC_KINDS = ['income', 'expense', 'refund']

/**
 * Text colour for the amount: green/red only for economic rows (or feeds without a
 * classification); transfers, debt payments and rows needing review stay neutral.
 */
function amountClass(tx) {
  if (hasFlowKind(tx) && !ECONOMIC_KINDS.includes(tx.reporting_flow_kind)) {
    return 'text-[var(--color-text-light)]'
  }
  if (tx.amount > 0) return 'text-[var(--color-accent-green)]'
  if (tx.amount < 0) return 'text-[var(--color-accent-red)]'
  return 'text-[var(--color-text-light)]'
}

/**
 * Generate initials from a name string (up to 2 chars).
 */
function initials(name) {
  if (!name) return '??'
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

/**
 * Normalize date display to YYYY-MM-DD.
 */
function formatDate(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    // If already ISO-like, take first 10 chars
    if (value.length >= 10 && /\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10)
    // Try to parse and reformat
    const d = new Date(value)
    if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10)
    return value
  }
  if (value instanceof Date && !isNaN(value.getTime())) {
    return value.toISOString().slice(0, 10)
  }
  return String(value)
}

/**
 * Resolve a user-friendly category label for modal rows.
 *
 * The dashboard category modal receives transactions from mixed endpoints,
 * so category text can arrive as `category_display`, `category_display_name`,
 * a plain string in `category`, or an array hierarchy. This helper normalizes
 * those shapes to ensure rows always show readable category text next to icons.
 *
 * @param {Record<string, unknown>} tx - Transaction row payload.
 * @returns {string} Human-readable category label.
 */
function getCategoryDisplayName(tx) {
  if (!tx) return ''

  const displayName =
    (typeof tx.category_display === 'string' && tx.category_display.trim()) ||
    (typeof tx.category_display_name === 'string' && tx.category_display_name.trim())

  if (displayName) return displayName

  if (Array.isArray(tx.category)) {
    const parts = tx.category
      .map((segment) => (typeof segment === 'string' ? segment.trim() : ''))
      .filter(Boolean)
    return parts.join(': ')
  }

  if (typeof tx.category === 'string') {
    return tx.category.trim()
  }

  return ''
}

/**
 * Resolve the primary text shown in the details column so callers can hide
 * redundant merchant labels in merchant-filtered modals.
 */
function rowPrimaryLabel(tx) {
  if (props.primaryField === 'description') {
    return tx?.description || tx?.merchant_name || '—'
  }
  return tx?.merchant_name || tx?.description || '—'
}

/**
 * Resolve the secondary text shown in the details column.
 */
function rowSecondaryLabel(tx) {
  if (props.primaryField === 'description') {
    return tx?.merchant_name || tx?.description || '—'
  }
  return tx?.description || tx?.merchant_name || '—'
}
</script>
