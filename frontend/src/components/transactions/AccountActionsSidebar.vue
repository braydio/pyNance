<template>
  <div class="space-y-5" data-testid="transactions-actions-sidebar">
    <Card class="p-4 space-y-4">
      <h3 class="text-sm font-semibold tracking-wide text-[var(--color-text-muted)] uppercase">
        Import Transactions
      </h3>
      <ImportFileSelector />
    </Card>

    <Card class="p-4 space-y-4">
      <div class="space-y-2">
        <label
          for="transactions-search"
          class="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]"
        >
          Search
        </label>
        <input
          id="transactions-search"
          v-model="searchModel"
          type="text"
          placeholder="Search transactions..."
          class="input w-full"
          data-testid="transactions-search"
        />
      </div>

      <div class="space-y-3">
        <DateRangeSelector
          :start-date="startDateModel"
          :end-date="endDateModel"
          disable-zoom
          @update:startDate="startDateModel = $event"
          @update:endDate="endDateModel = $event"
        />
        <AccountFilter v-model="accountModel" />
        <TypeSelector v-model="typeModel" />
      </div>
    </Card>

    <Card class="p-4 space-y-3">
      <div class="space-y-1">
        <h3 class="text-sm font-semibold tracking-wide text-[var(--color-text-muted)] uppercase">
          Transfer Scanner
        </h3>
        <p class="text-sm text-[var(--color-text-muted)]">
          Quickly flag potential internal transfers to reconcile accounts.
        </p>
      </div>
      <UiButton
        variant="outline"
        class="w-full"
        data-testid="open-scanner"
        @click="emit('open-scanner')"
      >
        Open Scanner
      </UiButton>
    </Card>
  </div>
</template>

<script setup>
/**
 * AccountActionsSidebar (transactions variant)
 * Sidebar providing file import, search filter, date/account/type selectors,
 * and quick access to the internal transfer scanner for the Transactions view.
 *
 * Props:
 * - search: current search string shared with the activity table
 * - startDate / endDate: ISO date bounds used for filtering the API
 * - accountId: active account filter
 * - txType: active transaction type filter (credit/debit)
 */
import { computed } from 'vue'
import ImportFileSelector from '@/components/forms/ImportFileSelector.vue'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import DateRangeSelector from '@/components/DateRangeSelector.vue'
import AccountFilter from '@/components/AccountFilter.vue'
import TypeSelector from '@/components/TypeSelector.vue'

const props = defineProps({
  /** Current search query */
  search: { type: String, default: '' },
  /** Lower date bound for filtering */
  startDate: { type: String, default: '' },
  /** Upper date bound for filtering */
  endDate: { type: String, default: '' },
  /** Selected account id filter */
  accountId: { type: String, default: '' },
  /** Selected transaction type filter */
  txType: { type: String, default: '' },
})

const emit = defineEmits([
  'update:search',
  'update:startDate',
  'update:endDate',
  'update:accountId',
  'update:txType',
  'open-scanner',
])

const searchModel = computed({
  get: () => props.search,
  set: (val) => emit('update:search', val),
})

const startDateModel = computed({
  get: () => props.startDate,
  set: (val) => emit('update:startDate', val),
})

const endDateModel = computed({
  get: () => props.endDate,
  set: (val) => emit('update:endDate', val),
})

const accountModel = computed({
  get: () => props.accountId,
  set: (val) => emit('update:accountId', val),
})

const typeModel = computed({
  get: () => props.txType,
  set: (val) => emit('update:txType', val),
})
</script>
