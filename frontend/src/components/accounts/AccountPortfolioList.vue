<!--
  AccountPortfolioList.vue
  Searchable, filterable ledger of accounts grouped by type then institution.
  Read-only: selecting an account emits `select`; there are no fetch/hide/delete controls.
-->
<template>
  <section
    class="portfolio-list"
    aria-labelledby="portfolio-list-title"
    data-testid="portfolio-list"
  >
    <header class="portfolio-list__header">
      <h2 id="portfolio-list-title" class="portfolio-list__title">Accounts</h2>
      <p class="portfolio-list__count" role="status" data-testid="portfolio-shown-count">
        Showing {{ visibleAccounts.length }} of {{ totalCount }}
        {{ totalCount === 1 ? 'account' : 'accounts' }}
      </p>
    </header>

    <div class="portfolio-filters">
      <label class="portfolio-field portfolio-field--search">
        <span class="portfolio-field__label">Search</span>
        <input
          type="search"
          class="input"
          placeholder="Name, institution or last 4 digits"
          :value="filters.query"
          data-testid="portfolio-search"
          @input="patch({ query: $event.target.value })"
        />
      </label>
      <label class="portfolio-field">
        <span class="portfolio-field__label">Institution</span>
        <select
          class="input"
          :value="filters.institution"
          data-testid="portfolio-institution"
          @change="patch({ institution: $event.target.value })"
        >
          <option value="all">All institutions</option>
          <option v-for="name in institutions" :key="name" :value="name">{{ name }}</option>
        </select>
      </label>
      <label class="portfolio-field">
        <span class="portfolio-field__label">Connection</span>
        <select
          class="input"
          :value="filters.connection"
          data-testid="portfolio-connection"
          @change="patch({ connection: $event.target.value })"
        >
          <option value="all">Any state</option>
          <option value="ok">Connected</option>
          <option value="needs_reconnect">Needs reconnect</option>
        </select>
      </label>
      <label class="portfolio-field">
        <span class="portfolio-field__label">Sort by</span>
        <select
          class="input"
          :value="filters.sort"
          data-testid="portfolio-sort"
          @change="patch({ sort: $event.target.value })"
        >
          <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </label>
      <label class="portfolio-check">
        <input
          type="checkbox"
          :checked="filters.includeHidden"
          data-testid="portfolio-include-hidden"
          @change="patch({ includeHidden: $event.target.checked })"
        />
        <span>Include hidden</span>
      </label>
    </div>

    <div v-if="activeChips.length" class="portfolio-active" data-testid="portfolio-active-filters">
      <button
        v-for="chip in activeChips"
        :key="chip.key"
        type="button"
        class="portfolio-active__chip"
        @click="patch(chip.clear)"
      >
        {{ chip.label }} <span aria-hidden="true">×</span>
        <span class="sr-only">Remove filter</span>
      </button>
      <button
        type="button"
        class="portfolio-active__reset"
        data-testid="portfolio-reset"
        @click="emit('reset')"
      >
        Reset
      </button>
    </div>

    <p v-if="!totalCount" class="portfolio-empty" data-testid="portfolio-empty">
      No accounts linked yet.
    </p>
    <p v-else-if="!visibleAccounts.length" class="portfolio-empty" data-testid="portfolio-no-match">
      No accounts match these filters.
    </p>

    <div v-else class="portfolio-ledger">
      <section
        v-for="group in ledger"
        :key="group.group"
        :data-testid="`ledger-group-${group.group}`"
      >
        <h3 class="portfolio-group-title">
          {{ group.label }} <span class="portfolio-group-count">{{ group.count }}</span>
        </h3>
        <div
          v-for="institution in group.institutions"
          :key="institution.name"
          class="portfolio-institution"
        >
          <h4 class="portfolio-institution__name">{{ institution.name }}</h4>
          <ul class="portfolio-rows">
            <li
              v-for="account in institution.accounts"
              :key="account.account_id"
              class="portfolio-row"
              :class="{
                'portfolio-row--selected': String(account.account_id) === String(selectedId),
              }"
              :data-testid="`portfolio-row-${account.account_id}`"
              :data-classification-conflict="classificationConflict(account) ? 'true' : null"
            >
              <div class="portfolio-row__identity">
                <p class="portfolio-row__name">
                  {{ account.display_name || account.name }}
                  <span v-if="account.is_hidden" class="portfolio-row__badge">Hidden</span>
                </p>
                <p class="portfolio-row__meta">
                  <span data-testid="row-type">{{ accountTypeLabel(account) }}</span>
                  {{ maskLabel(account) }}
                  <span
                    :class="{
                      'portfolio-row__warn': connectionState(account) === 'needs_reconnect',
                    }"
                  >
                    {{ syncStatus(account) }}
                  </span>
                </p>
              </div>

              <div class="portfolio-row__amount">
                <template v-if="isLiability(account)">
                  <p class="portfolio-row__value" data-testid="row-owed">
                    {{ owedLabel(account) }}
                  </p>
                  <p class="portfolio-row__sub">owed</p>
                </template>
                <template v-else>
                  <p class="portfolio-row__value" data-testid="row-balance">
                    {{ balanceLabel(account) }}
                  </p>
                </template>
              </div>

              <div
                v-if="classify(account) === 'credit'"
                class="portfolio-row__credit"
                data-testid="row-credit"
              >
                <template v-if="utilization(account)">
                  <div
                    class="portfolio-bar"
                    role="img"
                    :aria-label="`${utilization(account).percent}% of credit limit used`"
                  >
                    <span
                      class="portfolio-bar__fill"
                      :class="{ 'portfolio-bar__fill--over': utilization(account).overlimit }"
                      :style="{ width: Math.min(utilization(account).percent, 100) + '%' }"
                    ></span>
                  </div>
                  <p class="portfolio-row__sub">
                    {{ utilization(account).percent }}% of {{ formatAmount(limitOf(account)) }}
                    <strong v-if="utilization(account).overlimit">· over limit</strong>
                  </p>
                </template>
                <p v-else class="portfolio-row__sub">Credit limit unknown</p>
                <p v-if="availableLabel(account)" class="portfolio-row__sub">
                  {{ availableLabel(account) }}
                </p>
              </div>
              <div v-else class="portfolio-row__credit"></div>

              <div class="portfolio-row__apr" data-testid="row-apr">
                <template v-if="apr(account).applicable">
                  <p class="portfolio-row__value portfolio-row__value--sm">
                    {{ apr(account).value === null ? 'Unknown' : `${apr(account).value}%` }}
                  </p>
                  <p class="portfolio-row__sub">{{ aprCaption(account) }}</p>
                </template>
              </div>

              <button
                type="button"
                class="portfolio-row__action"
                :aria-label="`View details for ${account.display_name || account.name}`"
                :data-testid="`view-details-${account.account_id}`"
                @click="emit('select', account.account_id)"
              >
                View details
              </button>
            </li>
          </ul>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { formatAmount } from '@/utils/format'
import {
  GROUP_LABELS,
  SORT_OPTIONS,
  accountBalance,
  accountTypeLabel,
  accountUtilization,
  amountOwed,
  aprInfo,
  classificationConflict,
  classifyAccount,
  connectionState,
  creditLimit,
  filterPortfolioAccounts,
  groupAccountsForLedger,
  institutionOptions,
  isLiabilityGroup,
  sortPortfolioAccounts,
  syncStatus,
} from '@/utils/accountPortfolio'

const props = defineProps({
  accounts: { type: Array, default: () => [] },
  filters: {
    type: Object,
    default: () => ({
      query: '',
      group: 'all',
      institution: 'all',
      connection: 'all',
      sort: 'name',
      includeHidden: false,
    }),
  },
  selectedId: { type: [String, Number], default: null },
})
const emit = defineEmits(['update:filters', 'select', 'reset'])

const classify = classifyAccount
const utilization = accountUtilization
const apr = aprInfo
const limitOf = creditLimit

function patch(changes) {
  emit('update:filters', { ...props.filters, ...changes })
}

const totalCount = computed(
  () => props.accounts.filter((a) => props.filters.includeHidden || !a.is_hidden).length,
)
const institutions = computed(() => institutionOptions(props.accounts))
const visibleAccounts = computed(() =>
  sortPortfolioAccounts(filterPortfolioAccounts(props.accounts, props.filters), props.filters.sort),
)
const ledger = computed(() => groupAccountsForLedger(visibleAccounts.value))

const activeChips = computed(() => {
  const f = props.filters
  const chips = []
  if (f.group && f.group !== 'all')
    chips.push({ key: 'group', label: GROUP_LABELS[f.group], clear: { group: 'all' } })
  if (f.query) chips.push({ key: 'query', label: `“${f.query}”`, clear: { query: '' } })
  if (f.institution && f.institution !== 'all')
    chips.push({ key: 'institution', label: f.institution, clear: { institution: 'all' } })
  if (f.connection && f.connection !== 'all')
    chips.push({
      key: 'connection',
      label: f.connection === 'ok' ? 'Connected' : 'Needs reconnect',
      clear: { connection: 'all' },
    })
  if (f.includeHidden)
    chips.push({ key: 'hidden', label: 'Hidden included', clear: { includeHidden: false } })
  return chips
})

function isLiability(account) {
  return isLiabilityGroup(classifyAccount(account))
}

function maskLabel(account) {
  return account.mask ? `•••• ${account.mask}` : ''
}

function balanceLabel(account) {
  const balance = accountBalance(account)
  return balance === null ? 'Balance unknown' : formatAmount(balance)
}

function owedLabel(account) {
  const owed = amountOwed(account)
  return owed === null ? 'Unknown' : formatAmount(owed)
}

function availableLabel(account) {
  const provider = account.available_balance
  if (provider !== null && provider !== undefined) {
    return `${formatAmount(provider)} available`
  }
  const limit = creditLimit(account)
  const owed = amountOwed(account)
  if (limit !== null && owed !== null) {
    return `${formatAmount(Math.max(limit - owed, 0))} remaining (calculated)`
  }
  return ''
}

function aprCaption(account) {
  const info = aprInfo(account)
  return info.source === 'unknown' ? 'No verified rate' : info.label
}
</script>

<style scoped>
.portfolio-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.portfolio-list__header {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.portfolio-list__title {
  font-size: 1.15rem;
  font-weight: 700;
}

.portfolio-list__count {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.portfolio-filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 10rem), 1fr));
  gap: 0.6rem;
  align-items: end;
}

.portfolio-field {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.portfolio-field {
  min-width: 0;
}

.portfolio-field--search {
  grid-column: span 2;
}

/* Filters stay clear but lighter than the account results beneath them. */
.portfolio-field__label {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

.portfolio-check {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
}

.portfolio-active {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.portfolio-active__chip,
.portfolio-active__reset {
  padding: 0.15rem 0.6rem;
  border: 1px solid var(--themed-border);
  border-radius: 9999px;
  background: transparent;
  color: inherit;
  font-size: 0.875rem;
  cursor: pointer;
}

.portfolio-active__reset {
  color: var(--color-accent-cyan);
}

.portfolio-empty {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.portfolio-group-title {
  margin: 1rem 0 0.25rem;
  font-size: 1.1rem;
  font-weight: 700;
}

.portfolio-group-count {
  margin-left: 0.3rem;
  font-weight: 400;
  color: var(--color-text-muted);
}

/* Hierarchy: group > institution > account > primary amount > secondary details. */
.portfolio-institution__name {
  margin: 0.6rem 0 0.25rem;
  font-size: 1rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.portfolio-rows {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--divider);
  border-radius: 0.6rem;
  overflow: hidden;
}

.portfolio-row {
  display: grid;
  grid-template-columns:
    minmax(0, 2fr) minmax(7rem, 1fr) minmax(9rem, 1.2fr) minmax(6rem, 0.9fr)
    auto;
  gap: 0.75rem;
  align-items: center;
  padding: 0.7rem 0.9rem;
  border-top: 1px solid var(--divider);
}

.portfolio-row:first-child {
  border-top: 0;
}

.portfolio-row--selected {
  background: color-mix(in srgb, var(--color-accent-cyan) 10%, transparent);
}

.portfolio-row p {
  margin: 0;
}

.portfolio-row__name {
  font-size: 1rem;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.portfolio-row__badge {
  margin-left: 0.4rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  border: 1px solid var(--themed-border);
  border-radius: 4px;
  padding: 0 0.3rem;
}

.portfolio-row__meta,
.portfolio-row__sub {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  overflow-wrap: anywhere;
}

.portfolio-row__warn {
  color: var(--color-accent-yellow);
}

.portfolio-row__amount {
  text-align: right;
}

.portfolio-row__value {
  font-size: 1.15rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.portfolio-row__value--sm {
  font-size: 0.95rem;
}

.portfolio-bar {
  height: 0.35rem;
  border-radius: 9999px;
  background: color-mix(in srgb, var(--color-text-muted) 25%, transparent);
  overflow: hidden;
}

.portfolio-bar__fill {
  display: block;
  height: 100%;
  background: var(--color-accent-cyan);
}

.portfolio-bar__fill--over {
  background: var(--color-accent-red);
}

.portfolio-row__action {
  padding: 0.25rem 0.7rem;
  border: 1px solid var(--themed-border);
  border-radius: 0.4rem;
  background: transparent;
  color: var(--color-accent-cyan);
  font-size: 0.875rem;
  cursor: pointer;
}

.portfolio-row__action:focus-visible,
.portfolio-active__chip:focus-visible,
.portfolio-active__reset:focus-visible {
  outline: 2px solid var(--color-accent-cyan);
  outline-offset: 2px;
}

@media (max-width: 480px) {
  /* 390px phones: identity, amount and details each get a full-width line. */
  .portfolio-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .portfolio-row__identity,
  .portfolio-row__amount {
    grid-column: 1;
  }

  .portfolio-row__amount {
    text-align: left;
  }
}

@media (max-width: 768px) {
  .portfolio-field--search {
    grid-column: auto;
  }

  .portfolio-row {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .portfolio-row__value,
  .portfolio-row__sub {
    overflow-wrap: anywhere;
  }

  .portfolio-row__identity {
    grid-column: 1;
  }

  .portfolio-row__amount {
    grid-column: 2;
  }

  .portfolio-row__credit,
  .portfolio-row__apr,
  .portfolio-row__action {
    grid-column: 1 / -1;
  }

  .portfolio-row__action {
    justify-self: start;
  }
}
</style>
