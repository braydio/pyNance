<!-- Editable transactions table with category filtering and consistent row count -->
<template>
  <div class="transactions-table space-y-4">
    <!-- Category Filters -->
    <div class="flex items-center gap-4 category-filters">
      <select v-model="selectedPrimaryCategory" class="input">
        <option value="">All Categories</option>
        <option v-for="group in categoryTree" :key="group.name" :value="group.name">
          {{ group.name }}
        </option>
      </select>
      <select v-model="selectedSubcategory" class="input" :disabled="!selectedPrimaryCategory">
        <option value="">All Subcategories</option>
        <option v-for="child in subcategoryOptions" :key="child.id" :value="child.name">
          {{ child.name }}
        </option>
      </select>
    </div>

    <!-- Column Filter Controls -->
    <div class="field-filter-bar">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="field in filterableFields"
          :key="field.key"
          type="button"
          class="btn-sm filter-chip"
          :class="{ active: activeFilterKey === field.key }"
          @click="selectFilterField(field.key)"
        >
          Filter {{ field.label }}
        </button>
      </div>
      <div v-if="activeFilterKey" class="filter-input-row">
        <label class="text-xs font-semibold text-[var(--color-text-muted)]">
          Filtering by {{ activeFilterLabel }}
        </label>
        <div class="flex flex-wrap gap-2 items-center">
          <input
            ref="filterInputRef"
            v-model="fieldSearch"
            :list="`${activeFilterKey}-filters`"
            type="text"
            class="input"
            :placeholder="`Type to filter ${activeFilterLabel.toLowerCase()}…`"
          />
          <button
            type="button"
            class="btn-sm"
            :disabled="!fieldSearch.trim()"
            @click="addFieldFilter"
          >
            Add Filter
          </button>
          <button type="button" class="btn-sm clear-filter" @click="clearFieldFilter">Clear</button>
        </div>
        <datalist :id="`${activeFilterKey}-filters`">
          <option v-for="option in filteredFieldSuggestions" :key="option" :value="option" />
        </datalist>
      </div>
      <div v-if="activeFilterTags.length" class="active-filter-tags">
        <span v-for="filter in activeFilterTags" :key="filter.key" class="filter-tag">
          <span class="filter-tag__label">{{ filter.label }}:</span>
          <span class="filter-tag__value">{{ filter.value }}</span>
          <button type="button" class="filter-tag__remove" @click="removeFilterTag(filter.key)">
            ×
          </button>
        </span>
      </div>
    </div>

    <!-- Transactions Table -->
    <div class="table-shell overflow-hidden">
      <div
        ref="tableScrollRef"
        class="table-scroll max-h-[70vh] lg:max-h-[75vh] min-h-[50vh] sm:min-h-[55vh] overflow-auto"
      >
        <table class="transactions-grid min-w-full border-separate border-spacing-0 mt-2">
          <thead class="table-head sticky top-0 z-10">
            <tr>
              <th class="col-date" @click="sortBy('date')">
                Date <span v-if="sortKey === 'date'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-amount text-right" @click="sortBy('amount')">
                Amount
                <span v-if="sortKey === 'amount'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-description" @click="sortBy('description')">
                Description
                <span v-if="sortKey === 'description'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-category" @click="sortBy('category')">
                Category
                <span v-if="sortKey === 'category'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-merchant" @click="sortBy('merchant_name')">
                Merchant
                <span v-if="sortKey === 'merchant_name'">{{
                  sortOrder === 'asc' ? '▲' : '▼'
                }}</span>
              </th>
              <th class="col-account" @click="sortBy('account_name')">
                Account Name
                <span v-if="sortKey === 'account_name'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-institution" @click="sortBy('institution_name')">
                Institution
                <span v-if="sortKey === 'institution_name'">{{
                  sortOrder === 'asc' ? '▲' : '▼'
                }}</span>
              </th>
              <th class="col-subtype" @click="sortBy('subtype')">
                Subtype
                <span v-if="sortKey === 'subtype'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
              </th>
              <th class="col-actions">Actions</th>
              <th class="col-running" @click="sortBy('running_balance')">
                Running Balance
                <span v-if="sortKey === 'running_balance'">{{
                  sortOrder === 'asc' ? '▲' : '▼'
                }}</span>
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-if="useVirtualization && virtualPaddingTop" class="virtual-padding-row">
              <td :colspan="10" :style="{ height: `${virtualPaddingTop}px` }"></td>
            </tr>
            <tr
              v-for="row in rowsToRender"
              :key="row.tx.transaction_id"
              :class="getRowClasses(row.tx, row.renderIndex)"
            >
              <template v-if="row.tx._placeholder">
                <td v-for="n in 10" :key="n" class="px-4 py-3">&nbsp;</td>
              </template>
              <template v-else>
                <td class="col-date">
                  <input
                    v-if="editingIndex === row.renderIndex"
                    v-model="editBuffer.date"
                    type="date"
                    class="input"
                  />
                  <span v-else class="truncate">{{
                    formatDate(row.tx.date || row.tx.transaction_date)
                  }}</span>
                </td>
                <td class="col-amount">
                  <input
                    v-if="editingIndex === row.renderIndex"
                    v-model.number="editBuffer.amount"
                    type="number"
                    step="0.01"
                    class="input"
                  />
                  <span v-else class="truncate">{{ formatAmount(row.tx.amount) }}</span>
                </td>
                <td class="col-description">
                  <input
                    v-if="editingIndex === row.renderIndex"
                    v-model="editBuffer.description"
                    type="text"
                    class="input"
                  />
                  <span v-else class="truncate">{{ row.tx.description }}</span>
                </td>
                <td class="col-category">
                  <input
                    v-if="editingIndex === row.renderIndex"
                    v-model="editBuffer.category"
                    type="text"
                    list="category-suggestions"
                    class="input"
                    placeholder="Select or type category"
                  />
                  <span v-else>{{ row.tx.category }}</span>
                </td>
                <td class="px-4 py-3">
                  <input
                    v-if="editingIndex === row.renderIndex"
                    v-model="editBuffer.merchant_name"
                    type="text"
                    list="merchant-suggestions"
                    class="input"
                  />
                  <span v-else class="truncate">{{ row.tx.merchant_name }}</span>
                </td>
                <td class="col-account truncate">{{ row.tx.account_name || 'N/A' }}</td>
                <td class="col-institution truncate">{{ row.tx.institution_name || 'N/A' }}</td>
                <td class="col-subtype truncate">{{ row.tx.subtype || 'N/A' }}</td>
                <td class="col-actions">
                  <div class="flex flex-wrap gap-2 text-xs action-bar">
                    <template v-if="editingIndex === row.renderIndex">
                      <div class="flex flex-wrap gap-2 option-toggle-group">
                        <button
                          class="btn-sm option-toggle"
                          :class="{ active: row.tx.is_internal }"
                          @click="toggleInternal(row.tx)"
                        >
                          <span class="option-label">Internal Transfer</span>
                          <span
                            class="option-status"
                            :class="row.tx.is_internal ? 'status-marked' : 'status-unmarked'"
                          >
                            {{ row.tx.is_internal ? 'Marked' : 'Not Marked' }}
                          </span>
                        </button>
                        <button
                          class="btn-sm option-toggle"
                          :class="{ active: isRecurringMarked(row.tx) }"
                          @click="markRecurring(row.tx)"
                        >
                          <span class="option-label">Recurring Transaction</span>
                          <span
                            class="option-status"
                            :class="isRecurringMarked(row.tx) ? 'status-marked' : 'status-unmarked'"
                          >
                            {{ isRecurringMarked(row.tx) ? 'Marked' : 'Not Marked' }}
                          </span>
                        </button>
                      </div>
                      <div class="flex flex-wrap gap-2">
                        <button class="btn-sm" @click="saveEdit(row.tx)">Save</button>
                        <button class="btn-sm" @click="cancelEdit">Cancel</button>
                      </div>
                    </template>
                    <template v-else>
                      <button class="btn-sm" @click="startEdit(row.renderIndex, row.tx)">
                        Edit
                      </button>
                    </template>
                  </div>
                </td>
                <td class="col-running text-right font-mono">
                  <span v-if="row.tx.running_balance != null">{{
                    formatAmount(row.tx.running_balance)
                  }}</span>
                  <span v-else class="text-muted">—</span>
                </td>
              </template>
            </tr>
            <tr v-if="useVirtualization && virtualPaddingBottom" class="virtual-padding-row">
              <td :colspan="10" :style="{ height: `${virtualPaddingBottom}px` }"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!hasVisibleTransactions" class="text-center text-gray-500">
      No transactions found.
    </div>
    <Modal v-if="showInternalModal" @close="showInternalModal = false">
      <template #title>Select Internal Counterpart</template>
      <template #body>
        <div class="space-y-4">
          <FuzzyDropdown
            v-model="selectedCounterpart"
            :options="internalCandidates"
            :max="1"
            placeholder="Search transactions"
          />
          <div class="flex justify-end gap-2">
            <button class="btn-sm" @click="showInternalModal = false">Cancel</button>
            <button class="btn-sm" @click="confirmInternal">Confirm</button>
          </div>
        </div>
      </template>
    </Modal>
    <datalist id="category-suggestions">
      <option v-for="option in categorySuggestions" :key="option" :value="option" />
    </datalist>
    <datalist id="merchant-suggestions">
      <option v-for="name in merchantSuggestions" :key="name" :value="name" />
    </datalist>
  </div>
</template>

<script setup>
/**
 * UpdateTransactionsTable.vue
 *
 * Editable transaction table with filters, sorting, and virtualized rendering
 * for large transaction sets.
 */
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useVirtualizer } from '@tanstack/vue-virtual'
import Fuse from 'fuse.js'
import {
  updateTransaction,
  fetchMerchantSuggestions,
  createTransactionRule,
} from '@/api/transactions'
import { fetchCategoryTree } from '@/api/categories'
import { useToast } from 'vue-toastification'

import Modal from '@/components/ui/Modal.vue'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { formatAmount } from '@/utils/format'
const toast = useToast()
const emit = defineEmits(['editRecurringFromTransaction'])
const props = defineProps({
  transactions: {
    type: Array,
    default: () => [],
  },
  currentPage: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 15,
  },
})

const MIN_ROW_COUNT = 12
const VIRTUALIZATION_ROW_THRESHOLD = 80
const VIRTUAL_ROW_HEIGHT_PX = 56
const VIRTUAL_OVERSCAN = 8
const CATEGORY_SUGGESTION_LIMIT = 12

// Fields that may be edited by the user. All other transaction properties are locked.
const EDITABLE_FIELDS = ['date', 'amount', 'description', 'category', 'merchant_name']

const selectedPrimaryCategory = ref('')
const selectedSubcategory = ref('')
const editingIndex = ref(null)
const editingTransactionId = ref(null)
const editingTransactionSnapshot = ref(null)
const editBuffer = ref({
  date: '',
  amount: null,
  description: '',
  category: '',
  merchant_name: '',
})

// State for marking internal transactions
const showInternalModal = ref(false)
const internalCandidates = ref([])
const selectedCounterpart = ref([])
const activeInternalTx = ref(null)

const categoryTree = ref([])
const categoryOptions = ref([])
const merchantSuggestions = ref([])
const sortKey = ref('date')
const sortOrder = ref('desc')

const filterableFields = [
  { key: 'date', label: 'Date' },
  { key: 'description', label: 'Description' },
  { key: 'merchant_name', label: 'Merchant' },
  { key: 'account_name', label: 'Account' },
  { key: 'institution_name', label: 'Institution' },
  { key: 'category', label: 'Category' },
]

const activeFilterKey = ref('')
const fieldSearch = ref('')
const activeFieldFilters = ref([])
const filterInputRef = ref(null)
const tableScrollRef = ref(null)

const categoryFuse = computed(
  () =>
    new Fuse(
      categoryOptions.value.map((value) => ({ value })),
      {
        keys: ['value'],
        threshold: 0.3,
        ignoreLocation: true,
      },
    ),
)

const categorySuggestions = computed(() => {
  if (!categoryOptions.value.length) return []
  const query = (editBuffer.value.category || '').trim()
  if (!query) {
    return categoryOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  const seen = new Set()
  const matches = categoryFuse.value.search(query)
  const suggestions = []
  matches.forEach((match) => {
    if (!seen.has(match.item.value)) {
      suggestions.push(match.item.value)
      seen.add(match.item.value)
    }
  })
  if (!suggestions.length) {
    return categoryOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  return suggestions.slice(0, CATEGORY_SUGGESTION_LIMIT)
})

const subcategoryOptions = computed(() => {
  const selected = selectedPrimaryCategory.value?.toLowerCase()
  const group = categoryTree.value.find((g) => g.name?.toLowerCase() === selected)
  return group ? group.children : []
})

const filterSuggestions = computed(() => {
  if (!activeFilterKey.value) return []
  const seen = new Set()
  const values = []
  props.transactions.forEach((tx) => {
    const raw = tx[activeFilterKey.value]
    if (!raw) return
    const value = String(raw)
    if (seen.has(value)) return
    seen.add(value)
    values.push(value)
  })
  return values
})

const suggestionSearch = computed(
  () =>
    new Fuse(
      filterSuggestions.value.map((value) => ({ value })),
      {
        keys: ['value'],
        threshold: 0.35,
        ignoreLocation: true,
      },
    ),
)

const filteredFieldSuggestions = computed(() => {
  if (!activeFilterKey.value) return []
  const query = fieldSearch.value.trim()
  if (!query) return filterSuggestions.value.slice(0, 12)
  return suggestionSearch.value.search(query).map((r) => r.item.value)
})

const activeFilterLabel = computed(
  () => filterableFields.find((field) => field.key === activeFilterKey.value)?.label || '',
)

const activeFilterTags = computed(() => {
  const tags = []
  if (selectedPrimaryCategory.value) {
    tags.push({ key: 'primary', label: 'Category', value: selectedPrimaryCategory.value })
  }
  if (selectedSubcategory.value) {
    tags.push({ key: 'subcategory', label: 'Subcategory', value: selectedSubcategory.value })
  }
  activeFieldFilters.value.forEach((filter) => {
    tags.push({ key: `field:${filter.key}`, label: filter.label, value: filter.query })
  })
  return tags
})

/** Build row classes for standard, placeholder, and editing states. */
function getRowClasses(tx, index) {
  const base =
    'text-sm align-middle h-14 transition-colors text-[var(--color-text-light)] border-b last:border-b-0'
  if (tx._placeholder) {
    return [base, 'row-placeholder']
  }
  if (editingIndex.value === index) {
    return [base, 'row-editing']
  }
  return [base, index % 2 === 0 ? 'row-even' : 'row-odd']
}

function selectFilterField(key) {
  activeFilterKey.value = key
  const existing = activeFieldFilters.value.find((filter) => filter.key === key)
  fieldSearch.value = existing ? existing.query : ''
  nextTick(() => {
    if (filterInputRef.value) {
      filterInputRef.value.focus()
    }
  })
}

/**
 * Add or replace a field-level filter for the current key.
 */
function addFieldFilter() {
  const query = fieldSearch.value.trim()
  if (!activeFilterKey.value || !query) {
    return
  }
  const label = filterableFields.find((field) => field.key === activeFilterKey.value)?.label || ''
  const existingIndex = activeFieldFilters.value.findIndex(
    (filter) => filter.key === activeFilterKey.value,
  )
  const nextFilter = { key: activeFilterKey.value, label, query }
  if (existingIndex >= 0) {
    activeFieldFilters.value.splice(existingIndex, 1, nextFilter)
  } else {
    activeFieldFilters.value.push(nextFilter)
  }
  fieldSearch.value = ''
  activeFilterKey.value = ''
}

function clearFieldFilter() {
  fieldSearch.value = ''
  activeFilterKey.value = ''
}

/**
 * Remove an active filter tag by identifier.
 * @param {string} key - Filter tag identifier.
 */
function removeFilterTag(key) {
  if (key === 'primary') {
    selectedPrimaryCategory.value = ''
    selectedSubcategory.value = ''
    return
  }
  if (key === 'subcategory') {
    selectedSubcategory.value = ''
    return
  }
  if (key.startsWith('field:')) {
    const fieldKey = key.replace('field:', '')
    activeFieldFilters.value = activeFieldFilters.value.filter((filter) => filter.key !== fieldKey)
  }
}

/**
 * Build an edit buffer seeded with the transaction's current editable fields.
 *
 * @param {Object} tx - Transaction being edited.
 * @returns {Object} Prefilled edit buffer values.
 */
function buildEditBuffer(tx) {
  if (!tx) {
    return {
      date: '',
      amount: null,
      description: '',
      category: '',
      merchant_name: '',
    }
  }

  return {
    date: resolveTransactionDate(tx),
    amount: tx.amount ?? null,
    description: tx.description || '',
    category: tx.category || '',
    merchant_name: tx.merchant_name || '',
  }
}

/**
 * Cache the current transaction and editable values for the active row.
 *
 * @param {number} index - Rendered row index selected for editing.
 * @param {Object} tx - Transaction record associated with the row.
 */
function startEdit(index, tx) {
  editingTransactionId.value = tx?.transaction_id || null
  editingTransactionSnapshot.value = buildRuleContext(tx)
  editBuffer.value = buildEditBuffer(tx)
  editingIndex.value = index
}

/**
 * Reset editing state and clear cached transaction context.
 */
function cancelEdit() {
  editingIndex.value = null
  editingTransactionId.value = null
  editingTransactionSnapshot.value = null
  editBuffer.value = {
    date: '',
    amount: null,
    description: '',
    category: '',
    merchant_name: '',
  }
}

function isValidDate(value) {
  const d = new Date(value)
  return !isNaN(d.getTime())
}

function resolveTransactionDate(tx) {
  return tx?.date || tx?.transaction_date || ''
}

/**
 * Retrieve a transaction by identifier from the current prop set.
 *
 * @param {string|null} transactionId - Identifier to match.
 * @returns {Object|null} Matching transaction object, if found.
 */
function findTransactionById(transactionId) {
  if (!transactionId) return null
  return (
    props.transactions.find((transaction) => transaction.transaction_id === transactionId) || null
  )
}

/**
 * Build a minimal snapshot used for rule prompts when saving edits.
 *
 * @param {Object|null} tx - Transaction to snapshot.
 * @returns {Object|null} Snapshot containing identifiers and display fields.
 */
function buildRuleContext(tx) {
  if (!tx) return null
  return {
    transaction_id: tx.transaction_id,
    user_id: tx.user_id || '',
    account_id: tx.account_id,
    description: tx.description || '',
    account_name: tx.account_name || '',
    institution_name: tx.institution_name || '',
  }
}

/**
 * Persist edits for the active transaction and optionally create a rule.
 *
 * @param {Object} tx - Transaction reference from the current row.
 */
async function saveEdit(tx) {
  try {
    const activeTx = findTransactionById(editingTransactionId.value) || tx
    if (!activeTx) {
      toast.error('Unable to locate transaction to update.')
      return
    }

    const payload = { transaction_id: activeTx.transaction_id }
    EDITABLE_FIELDS.forEach((field) => {
      const currentValue = field === 'date' ? resolveTransactionDate(activeTx) : activeTx[field]
      if (editBuffer.value[field] !== currentValue) {
        payload[field] = editBuffer.value[field]
      }
    })

    if (Object.keys(payload).length === 1) {
      toast.info('No changes to save')
      return
    }

    if (payload.date && !isValidDate(payload.date)) {
      toast.error('Invalid date format')
      return
    }

    if (payload.amount != null && isNaN(Number(payload.amount))) {
      toast.error('Invalid amount')
      return
    }

    await updateTransaction(payload)
    const changes = { ...payload }
    delete changes.transaction_id
    Object.assign(activeTx, changes)
    editingIndex.value = null
    const ruleSource = {
      ...(editingTransactionSnapshot.value || buildRuleContext(activeTx) || {}),
      ...changes,
      description: editBuffer.value.description ?? activeTx.description ?? '',
      account_name: activeTx.account_name ?? '',
      institution_name: activeTx.institution_name ?? '',
    }
    const accountLabel = ruleSource.account_name || 'this account'
    const institutionLabel = ruleSource.institution_name || 'this institution'
    editingTransactionId.value = null
    editingTransactionSnapshot.value = null
    toast.success('Transaction updated')

    // Offer to save a rule for future matches when key fields change
    const changedField = ['category', 'merchant_name', 'merchant_type'].find((f) => f in payload)
    if (changedField) {
      const newValue = payload[changedField]
      const promptText = [
        `Always set ${changedField} to "${newValue}" for ${ruleSource.description}`,
        `in ${accountLabel} at ${institutionLabel}?`,
      ].join(' ')
      if (confirm(promptText)) {
        try {
          await createTransactionRule({
            user_id: ruleSource.user_id || '',
            field: changedField,
            value: newValue,
            description: ruleSource.description,
            account_id: ruleSource.account_id,
          })
          toast.success('Rule saved')
        } catch (e) {
          console.error('Failed to save rule:', e)
          toast.error('Failed to save rule')
        }
      }
    }
  } catch (e) {
    console.error('Failed to save edit:', e)
    toast.error('Failed to update transaction.')
  }
}

function isRecurringMarked(tx) {
  return Boolean(tx?.is_recurring || tx?.recurrence_rule || tx?.recurring_transaction_id)
}

/**
 * Mark a transaction as recurring and emit the edit flow.
 *
 * @param {Object} tx - Transaction to mark recurring.
 */
function markRecurring(tx) {
  toast.success('Marked as recurring')
  emit('editRecurringFromTransaction', tx)
  if (!isRecurringMarked(tx)) {
    tx.is_recurring = true
  }
}

async function toggleInternal(tx) {
  try {
    if (!tx.is_internal) {
      // Prepare modal with candidate counterpart transactions
      activeInternalTx.value = tx
      selectedCounterpart.value = []
      internalCandidates.value = props.transactions
        .filter(
          (t) =>
            t.transaction_id !== tx.transaction_id &&
            !t.is_internal &&
            Math.abs((t.amount || 0) + (tx.amount || 0)) <= 0.01,
        )
        .map((t) => ({
          id: t.transaction_id,
          name: `${t.date} ${t.description} ${formatAmount(t.amount)}`,
        }))
      showInternalModal.value = true
    } else {
      await updateTransaction({
        transaction_id: tx.transaction_id,
        is_internal: false,
        counterpart_transaction_id: tx.internal_match_id || null,
        flag_counterpart: true,
      })
      tx.is_internal = false
      const counterpart = props.transactions.find((t) => t.transaction_id === tx.internal_match_id)
      if (counterpart) counterpart.is_internal = false
      toast.success('Unmarked internal')
    }
  } catch (e) {
    console.error('Failed to toggle internal flag:', e)
    toast.error('Failed to update internal flag')
  }
}

/** Confirm selection of counterpart transaction and mark both as internal. */
async function confirmInternal() {
  try {
    if (!activeInternalTx.value) return
    const counterpartId = selectedCounterpart.value[0]
    if (!counterpartId) {
      toast.error('Select a counterpart transaction')
      return
    }
    await updateTransaction({
      transaction_id: activeInternalTx.value.transaction_id,
      is_internal: true,
      counterpart_transaction_id: counterpartId,
      flag_counterpart: true,
    })
    activeInternalTx.value.is_internal = true
    activeInternalTx.value.internal_match_id = counterpartId
    const counterpart = props.transactions.find((t) => t.transaction_id === counterpartId)
    if (counterpart) {
      counterpart.is_internal = true
      counterpart.internal_match_id = activeInternalTx.value.transaction_id
    }
    toast.success('Marked as internal')
  } catch (e) {
    console.error('Failed to mark internal:', e)
    toast.error('Failed to mark internal')
  } finally {
    showInternalModal.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: '2-digit',
    month: 'short',
    day: 'numeric',
  })
}

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = key === 'date' || key === 'amount' ? 'desc' : 'asc'
  }
}

const filteredTransactions = computed(() => {
  let txs = [...props.transactions]
  if (activeFieldFilters.value.length) {
    activeFieldFilters.value.forEach((filter) => {
      const query = filter.query.trim()
      if (!query) return
      const columnFuse = new Fuse(txs, {
        keys: [filter.key],
        threshold: 0.35,
        ignoreLocation: true,
      })
      txs = columnFuse.search(query).map((r) => r.item)
    })
  }
  // Primary category filter if selected
  if (selectedPrimaryCategory.value) {
    const primary = selectedPrimaryCategory.value.toLowerCase()
    txs = txs.filter((tx) => (tx.category || '').toLowerCase().startsWith(primary))
  }
  // Subcategory filter further narrows
  if (selectedSubcategory.value) {
    txs = txs.filter((tx) =>
      tx.category?.toLowerCase().includes(selectedSubcategory.value.toLowerCase()),
    )
  } else if (selectedPrimaryCategory.value) {
    txs = txs.filter(
      (tx) => tx.primary_category?.toLowerCase() === selectedPrimaryCategory.value.toLowerCase(),
    )
  }
  // Sort, with case-insensitive compare for strings
  txs.sort((a, b) => {
    const aVal = a[sortKey.value]
    const bVal = b[sortKey.value]
    if (typeof aVal === 'string' || typeof bVal === 'string') {
      return (
        (sortOrder.value === 'asc' ? 1 : -1) *
        String(aVal || '').localeCompare(String(bVal || ''), undefined, { sensitivity: 'base' })
      )
    }
    const aNum = aVal ?? 0
    const bNum = bVal ?? 0
    return (sortOrder.value === 'asc' ? 1 : -1) * (aNum > bNum ? 1 : aNum < bNum ? -1 : 0)
  })
  return txs
})

const paginatedFilteredTransactions = computed(() => {
  const start = (props.currentPage - 1) * props.pageSize
  return filteredTransactions.value.slice(start, start + props.pageSize)
})

// Maintain a steady table height even when searches return few results.
const baseRowCount = computed(() =>
  Math.max(MIN_ROW_COUNT, props.pageSize, paginatedFilteredTransactions.value.length),
)

const displayTransactions = computed(() => {
  // Pad to preserve table height for small datasets.
  const padded = paginatedFilteredTransactions.value.slice(
    0,
    paginatedFilteredTransactions.value.length,
  )
  const targetLength = Math.max(baseRowCount.value, padded.length)
  while (padded.length < targetLength) {
    padded.push({ _placeholder: true, transaction_id: `placeholder-${padded.length}` })
  }
  return padded
})

const useVirtualization = computed(
  () => paginatedFilteredTransactions.value.length > VIRTUALIZATION_ROW_THRESHOLD,
)

const rowVirtualizer = useVirtualizer(
  computed(() => ({
    count: paginatedFilteredTransactions.value.length,
    getScrollElement: () => tableScrollRef.value,
    estimateSize: () => VIRTUAL_ROW_HEIGHT_PX,
    overscan: VIRTUAL_OVERSCAN,
  })),
)

const virtualRows = computed(() =>
  rowVirtualizer.value.getVirtualItems().map((row) => ({
    ...row,
    tx: paginatedFilteredTransactions.value[row.index],
  })),
)

const virtualPaddingTop = computed(() => {
  if (!useVirtualization.value || virtualRows.value.length === 0) return 0
  return virtualRows.value[0].start
})

const virtualPaddingBottom = computed(() => {
  if (!useVirtualization.value || virtualRows.value.length === 0) return 0
  const lastRow = virtualRows.value[virtualRows.value.length - 1]
  // Padding rows preserve scroll height while rendering only visible items.
  return rowVirtualizer.value.getTotalSize() - lastRow.end
})

const rowsToRender = computed(() => {
  if (useVirtualization.value) {
    return virtualRows.value.map((row) => ({ tx: row.tx, renderIndex: row.index }))
  }
  return displayTransactions.value.map((tx, index) => ({ tx, renderIndex: index }))
})

const hasVisibleTransactions = computed(() => filteredTransactions.value.length > 0)

// Reset subcategory when primary category changes to avoid stale filters
watch(selectedPrimaryCategory, () => {
  selectedSubcategory.value = ''
})

onMounted(async () => {
  try {
    await loadCategoryData()
    // Fetch merchant suggestions for autocomplete
    merchantSuggestions.value = await fetchMerchantSuggestions('')
  } catch (e) {
    console.error('Failed to load category tree:', e)
  }
})

/**
 * Flatten the category tree into unique suggestion labels.
 *
 * @param {Array<Object>} groups - Category groups with children.
 * @returns {string[]} Sorted list of suggestion labels.
 */
function buildCategoryOptions(groups = []) {
  const suggestions = []
  groups.forEach((group) => {
    if (group.name) {
      suggestions.push(group.name)
    }
    group.children.forEach((child) => {
      if (!child.name) return
      suggestions.push(child.name)
      suggestions.push(`${group.name}: ${child.name}`)
    })
  })
  const unique = Array.from(new Set(suggestions.filter(Boolean)))
  return unique.sort((a, b) => a.localeCompare(b))
}

/**
 * Fetch and normalize category data for filtering and autocomplete.
 */
async function loadCategoryData() {
  const res = await fetchCategoryTree()
  if (res?.status === 'success') {
    const tree = (res.data || []).map((group) => {
      const groupName = group.label || group.name
      const children = (group.children || [])
        .map((child) => ({
          id: child.id,
          name: child.label || child.name,
          plaid_id: child.plaid_id || null,
        }))
        .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
      return {
        id: group.id,
        name: groupName,
        children,
      }
    })
    categoryTree.value = tree.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    categoryOptions.value = buildCategoryOptions(categoryTree.value)
    return
  }
  categoryTree.value = []
  categoryOptions.value = []
}
</script>

<style scoped>
@reference "../../assets/css/main.css";

.transactions-table {
  background: var(--color-bg-secondary);
  border: 1.5px solid var(--divider);
  border-radius: 1.5rem;
  padding: 1.5rem;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.2);
  color: var(--color-text-light);
}

.input {
  @apply w-full px-3 py-2 rounded-lg border text-sm shadow-inner;
  background: var(--input-bg);
  color: var(--color-text-light);
  border-color: var(--divider);
}

.input:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(113, 156, 214, 0.35);
}

.btn-sm {
  @apply inline-flex items-center px-3 py-1.5 text-xs font-semibold rounded-lg transition shadow-sm;
  background: linear-gradient(135deg, var(--color-accent-purple), var(--color-accent-cyan));
  color: #0f172a;
  border: none;
}

.btn-sm:hover {
  filter: brightness(1.03);
  box-shadow: 0 10px 30px rgba(99, 102, 241, 0.18);
}

.btn-sm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.table-shell {
  background: var(--table-surface);
  border: 1.5px solid var(--table-border);
  border-radius: 1.5rem;
  box-shadow: 0 14px 48px rgba(0, 0, 0, 0.18);
}

.table-scroll {
  background: var(--table-surface-alt);
}

.transactions-grid {
  table-layout: fixed;
  color: var(--color-text-light);
}

.transactions-grid th,
.transactions-grid td {
  padding: 0.75rem 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-color: var(--table-border);
}

.transactions-grid tr {
  border-bottom: 1px solid var(--table-border);
}

.table-head {
  background: var(--table-header);
  color: var(--color-text-light);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.table-head th {
  cursor: pointer;
  text-align: left;
}

.col-date {
  width: 120px;
}

.col-amount {
  width: 120px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-description {
  width: 240px;
}

.col-category,
.col-merchant,
.col-account,
.col-institution,
.col-subtype {
  width: 160px;
}

.col-actions {
  width: 220px;
}

.col-running {
  width: 160px;
}

.row-placeholder {
  background: transparent;
}

.row-editing {
  background: rgba(113, 156, 214, 0.12);
}

.row-even {
  background: var(--table-surface);
}

.row-odd {
  background: var(--table-surface-alt);
}

.row-even:hover,
.row-odd:hover {
  background: var(--table-hover);
}

.virtual-padding-row td {
  padding: 0;
  border: 0;
}

.action-bar {
  color: var(--color-text-muted);
}

.field-filter-bar {
  @apply flex flex-col gap-2;
  padding: 0.75rem 1rem;
  border: 1px dashed var(--divider);
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.04);
}

.filter-chip {
  background: rgba(113, 156, 214, 0.12);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
}

.filter-chip.active {
  box-shadow: 0 0 0 1px var(--color-accent-purple);
  background: rgba(113, 156, 214, 0.24);
}

.filter-input-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.active-filter-tags {
  @apply flex flex-wrap items-center gap-2;
}

.filter-tag {
  @apply inline-flex items-center gap-2 rounded-full border border-[var(--divider)];
  @apply bg-[rgba(113,156,214,0.12)] px-3 py-1 text-xs text-[var(--color-text-light)];
}

.filter-tag__label {
  @apply uppercase tracking-wide text-[11px] text-[var(--color-text-muted)];
}

.filter-tag__value {
  @apply font-semibold text-[var(--color-text-light)];
}

.filter-tag__remove {
  @apply text-[var(--color-text-muted)] hover:text-[var(--color-text-light)] transition;
}

.clear-filter {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
}

.category-filters {
  margin-bottom: 0.75rem;
}

.option-toggle-group {
  width: 100%;
}

.option-toggle {
  @apply justify-between;
  border: 1px solid var(--divider);
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-text-light);
  min-width: 230px;
}

.option-toggle.active {
  box-shadow: 0 0 0 1px var(--color-accent-purple);
  background: rgba(113, 156, 214, 0.18);
}

.option-label {
  font-weight: 700;
}

.option-status {
  @apply inline-flex items-center px-2 py-1 rounded-md text-[11px] font-semibold;
  border: 1px solid var(--divider);
}

.status-marked {
  color: var(--color-accent-green, #34d399);
  background: rgba(52, 211, 153, 0.12);
  border-color: rgba(52, 211, 153, 0.4);
}

.status-unmarked {
  color: var(--color-text-muted);
  background: rgba(255, 255, 255, 0.04);
}
</style>
