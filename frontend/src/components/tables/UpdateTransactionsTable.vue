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

    <!-- Transactions Table -->
    <div class="table-shell overflow-hidden">
      <div class="table-scroll max-h-[640px] min-h-[520px] overflow-auto">
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
            <tr
              v-for="(tx, index) in displayTransactions"
              :key="tx.transaction_id"
              :class="[
                'text-sm align-middle h-14 transition-colors text-[var(--color-text-light)] border-b last:border-b-0',
                tx._placeholder
                  ? 'row-placeholder'
                  : editingIndex === index
                    ? 'row-editing'
                    : index % 2 === 0
                      ? 'row-even'
                      : 'row-odd',
              ]"
            >
              <template v-if="tx._placeholder">
                <td v-for="n in 10" :key="n" class="px-4 py-3">&nbsp;</td>
              </template>
              <template v-else>
                <td class="col-date">
                  <input
                    v-if="editingIndex === index"
                    v-model="editBuffer.date"
                    type="date"
                    class="input"
                  />
                  <span v-else class="truncate">{{ formatDate(tx.date) }}</span>
                </td>
                <td class="col-amount">
                  <input
                    v-if="editingIndex === index"
                    v-model.number="editBuffer.amount"
                    type="number"
                    step="0.01"
                    class="input"
                  />
                  <span v-else class="truncate">{{ formatAmount(tx.amount) }}</span>
                </td>
                <td class="col-description">
                  <input
                    v-if="editingIndex === index"
                    v-model="editBuffer.description"
                    type="text"
                    class="input"
                  />
                  <span v-else class="truncate">{{ tx.description }}</span>
                </td>
                <td class="col-category">
                  <input
                    v-if="editingIndex === index"
                    v-model="editBuffer.category"
                    type="text"
                    list="category-suggestions"
                    class="input"
                    placeholder="Select or type category"
                  />
                  <span v-else>{{ tx.category }}</span>
                </td>
                <td class="px-4 py-3">
                  <input
                    v-if="editingIndex === index"
                    v-model="editBuffer.merchant_name"
                    type="text"
                    list="merchant-suggestions"
                    class="input"
                  />
                  <span v-else class="truncate">{{ tx.merchant_name }}</span>
                </td>
                <td class="col-account truncate">{{ tx.account_name || 'N/A' }}</td>
                <td class="col-institution truncate">{{ tx.institution_name || 'N/A' }}</td>
                <td class="col-subtype truncate">{{ tx.subtype || 'N/A' }}</td>
                <td class="col-actions">
                  <div class="flex flex-wrap gap-2 text-xs action-bar">
                    <template v-if="editingIndex === index">
                      <div class="flex flex-wrap gap-2 option-toggle-group">
                        <button
                          class="btn-sm option-toggle"
                          :class="{ active: tx.is_internal }"
                          @click="toggleInternal(tx)"
                        >
                          <span class="option-label">Internal Transfer</span>
                          <span
                            class="option-status"
                            :class="tx.is_internal ? 'status-marked' : 'status-unmarked'"
                          >
                            {{ tx.is_internal ? 'Marked' : 'Not Marked' }}
                          </span>
                        </button>
                        <button
                          class="btn-sm option-toggle"
                          :class="{ active: isRecurringMarked(tx) }"
                          @click="markRecurring(index)"
                        >
                          <span class="option-label">Recurring Transaction</span>
                          <span
                            class="option-status"
                            :class="isRecurringMarked(tx) ? 'status-marked' : 'status-unmarked'"
                          >
                            {{ isRecurringMarked(tx) ? 'Marked' : 'Not Marked' }}
                          </span>
                        </button>
                      </div>
                      <div class="flex flex-wrap gap-2">
                        <button class="btn-sm" @click="saveEdit(tx)">Save</button>
                        <button class="btn-sm" @click="cancelEdit">Cancel</button>
                      </div>
                    </template>
                    <template v-else>
                      <button class="btn-sm" @click="startEdit(index, tx)">Edit</button>
                    </template>
                  </div>
                </td>
                <td class="col-running text-right font-mono">
                  <span v-if="tx.running_balance != null">{{ formatAmount(tx.running_balance) }}</span>
                  <span v-else class="text-muted">—</span>
                </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="displayTransactions.every((tx) => tx._placeholder)"
      class="text-center text-gray-500"
    >
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
import { ref, computed, onMounted, watch } from 'vue'
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
})

const MIN_ROW_COUNT = 12

// Fields that may be edited by the user. All other transaction properties are locked.
const EDITABLE_FIELDS = ['date', 'amount', 'description', 'category', 'merchant_name']

const selectedPrimaryCategory = ref('')
const selectedSubcategory = ref('')
const editingIndex = ref(null)
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
const merchantSuggestions = ref([])
const sortKey = ref('date')
const sortOrder = ref('asc')

const categorySuggestions = computed(() => {
  const seen = new Set()
  const suggestions = []
  categoryTree.value.forEach((group) => {
    if (group.name && !seen.has(group.name)) {
      suggestions.push(group.name)
      seen.add(group.name)
    }
    group.children.forEach((child) => {
      if (child.name && !seen.has(child.name)) {
        suggestions.push(child.name)
        seen.add(child.name)
      }
    })
  })
  return suggestions.sort((a, b) => a.localeCompare(b))
})

const subcategoryOptions = computed(() => {
  const selected = selectedPrimaryCategory.value?.toLowerCase()
  const group = categoryTree.value.find((g) => g.name?.toLowerCase() === selected)
  return group ? group.children : []
})

// Maintain a steady table height even when searches return few results.
const baseRowCount = computed(() => Math.max(MIN_ROW_COUNT, props.transactions.length))

function startEdit(index, tx) {
  editingIndex.value = index
  editBuffer.value = { ...tx }
}

function cancelEdit() {
  editingIndex.value = null
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

async function saveEdit(tx) {
  try {
    const payload = { transaction_id: tx.transaction_id }
    EDITABLE_FIELDS.forEach((field) => {
      if (editBuffer.value[field] !== tx[field]) {
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
    Object.assign(tx, changes)
    editingIndex.value = null
    toast.success('Transaction updated')

    // Offer to save a rule for future matches when key fields change
    const changedField = ['category', 'merchant_name', 'merchant_type'].find((f) => f in payload)
    if (changedField) {
      const newValue = payload[changedField]
      const promptText = `Always set ${changedField} to "${newValue}" for ${tx.description} in ${tx.account_name} at ${tx.institution_name}?`
      if (confirm(promptText)) {
        try {
          await createTransactionRule({
            user_id: tx.user_id || '',
            field: changedField,
            value: newValue,
            description: tx.description,
            account_id: tx.account_id,
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

function markRecurring(index) {
  const tx = props.transactions[index]
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
    sortOrder.value = 'asc'
  }
}

const displayTransactions = computed(() => {
  let txs = [...props.transactions]
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
  // pad to preserve table height
  const padded = txs.slice(0, txs.length)
  const targetLength = Math.max(baseRowCount.value, txs.length)
  while (padded.length < targetLength) {
    padded.push({ _placeholder: true, transaction_id: `placeholder-${padded.length}` })
  }
  return padded
})

// Reset subcategory when primary category changes to avoid stale filters
watch(selectedPrimaryCategory, () => {
  selectedSubcategory.value = ''
})

onMounted(async () => {
  try {
    const res = await fetchCategoryTree()
    if (res?.status === 'success') {
      const tree = (res.data || []).map((group) => {
        const children = (group.children || [])
          .map((child) => ({
            id: child.id,
            name: child.label,
            plaid_id: child.plaid_id || null,
          }))
          .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        return {
          id: group.id,
          name: group.label,
          children,
        }
      })
      categoryTree.value = tree.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    }
    // Fetch merchant suggestions for autocomplete
    merchantSuggestions.value = await fetchMerchantSuggestions('')
  } catch (e) {
    console.error('Failed to load category tree:', e)
  }
})
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
  background: var(--color-bg-secondary);
  border: 1.5px solid var(--divider);
  border-radius: 1.5rem;
  box-shadow: 0 14px 48px rgba(0, 0, 0, 0.18);
}

.table-scroll {
  background: linear-gradient(180deg, rgba(41, 57, 79, 0.9), rgba(33, 46, 63, 0.92));
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
  border-color: var(--divider);
}

.transactions-grid tr {
  border-bottom: 1px solid var(--divider);
}

.table-head {
  background: rgba(57, 80, 109, 0.45);
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
  background: rgba(33, 46, 63, 0.65);
}

.row-odd {
  background: rgba(41, 57, 79, 0.7);
}

.row-even:hover,
.row-odd:hover {
  background: rgba(113, 156, 214, 0.18);
}

.action-bar {
  color: var(--color-text-muted);
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
