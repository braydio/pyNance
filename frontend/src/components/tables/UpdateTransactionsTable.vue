<!-- Editable transactions table with category filtering and consistent row count -->
<template>
  <div class="card space-y-4">
    <!-- Category Filters -->
    <div class="flex items-center gap-4">
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
    <table class="min-w-full divide-y mt-4">
      <thead class="text-sm font-semibold uppercase">
        <tr>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('date')">
            Date <span v-if="sortKey === 'date'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('amount')">
            Amount <span v-if="sortKey === 'amount'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('description')">
            Description
            <span v-if="sortKey === 'description'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('category')">
            Category
            <span v-if="sortKey === 'category'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('merchant_name')">
            Merchant
            <span v-if="sortKey === 'merchant_name'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('account_name')">
            Account Name
            <span v-if="sortKey === 'account_name'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('institution_name')">
            Institution
            <span v-if="sortKey === 'institution_name'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2 cursor-pointer" @click="sortBy('subtype')">
            Subtype <span v-if="sortKey === 'subtype'">{{ sortOrder === 'asc' ? '▲' : '▼' }}</span>
          </th>
          <th class="px-3 py-2">Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="(tx, index) in displayTransactions"
          :key="tx.transaction_id"
          :class="[
            'text-sm',
            tx._placeholder
              ? ''
              : editingIndex === index
                ? 'bg-[var(--color-bg-sec)]'
                : 'hover:bg-[var(--hover)-light]',
          ]"
        >
          <template v-if="tx._placeholder">
            <td v-for="n in 9" :key="n" class="px-3 py-2">&nbsp;</td>
          </template>
          <template v-else>
            <td class="px-3 py-2">
              <input
                v-if="editingIndex === index"
                v-model="editBuffer.date"
                type="date"
                class="input"
              />
              <span v-else>{{ formatDate(tx.date) }}</span>
            </td>
            <td class="px-3 py-2">
              <input
                v-if="editingIndex === index"
                v-model.number="editBuffer.amount"
                type="number"
                step="0.01"
                class="input"
              />
              <span v-else>{{ formatAmount(tx.amount) }}</span>
            </td>
            <td class="px-3 py-2">
              <input
                v-if="editingIndex === index"
                v-model="editBuffer.description"
                type="text"
                class="input"
              />
              <span v-else>{{ tx.description }}</span>
            </td>
            <td class="px-3 py-2">
              <select v-if="editingIndex === index" v-model="editBuffer.category" class="input">
                <option disabled value="">-- Select Category --</option>
                <optgroup v-for="group in categoryTree" :label="group.name" :key="group.name">
                  <option v-for="child in group.children" :key="child.id" :value="child.name">
                    {{ child.name }}
                  </option>
                </optgroup>
              </select>
              <span v-else>{{ tx.category }}</span>
            </td>
            <td class="px-3 py-2">
              <input
                v-if="editingIndex === index"
                v-model="editBuffer.merchant_name"
                type="text"
                class="input"
              />
              <span v-else>{{ tx.merchant_name }}</span>
            </td>
            <td class="px-3 py-2">{{ tx.account_name || 'N/A' }}</td>
            <td class="px-3 py-2">{{ tx.institution_name || 'N/A' }}</td>
            <td class="px-3 py-2">{{ tx.subtype || 'N/A' }}</td>
            <td class="px-3 py-2 space-x-1">
              <template v-if="editingIndex === index">
                <button class="btn-sm" @click="saveEdit(tx)">Save</button>
                <button class="btn-sm" @click="cancelEdit">Cancel</button>
              </template>
              <template v-else>
                <button class="btn-sm" @click="startEdit(index, tx)">Edit</button>
                <button class="btn-sm" @click="markRecurring(index)">Recurring</button>
                <button class="btn-sm" @click="toggleInternal(tx)">
                  {{ tx.is_internal ? 'Unmark Internal' : 'Mark Internal' }}
                </button>
              </template>
            </td>
          </template>
        </tr>
      </tbody>
    </table>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { updateTransaction } from '@/api/transactions'
import { useToast } from 'vue-toastification'

import Modal from '@/components/ui/Modal.vue'
import FuzzyDropdown from '@/components/ui/FuzzyDropdown.vue'
import { formatAmount } from '@/utils/format'
const toast = useToast()
const emit = defineEmits(['editRecurringFromTransaction'])
const props = defineProps({ transactions: Array })

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
const sortKey = ref('date')
const sortOrder = ref('asc')

const subcategoryOptions = computed(() => {
  const group = categoryTree.value.find((g) => g.name === selectedPrimaryCategory.value)
  return group ? group.children : []
})

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

    if (payload.description) {
      const confirmed = confirm(
        `Always use description "${payload.description}" for merchant "${tx.merchant_name}" on account "${tx.account_name}"?`,
      )
      if (confirmed) {
        console.log('[RuleEngine] Create rule: if merchant is', tx.merchant_name)
      }
    }
  } catch (e) {
    console.error('Failed to save edit:', e)
    toast.error('Failed to update transaction.')
  }
}

function markRecurring(index) {
  const tx = props.transactions[index]
  toast.success('Marked as recurring')
  emit('editRecurringFromTransaction', tx)
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
      const counterpart = props.transactions.find(
        (t) => t.transaction_id === tx.internal_match_id,
      )
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
    const counterpart = props.transactions.find(
      (t) => t.transaction_id === counterpartId,
    )
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
  const padded = txs.slice(0, props.transactions.length)
  while (padded.length < props.transactions.length) {
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
    const res = await axios.get('/api/categories/tree')
    if (res.data?.status === 'success') {
      categoryTree.value = res.data.data
    }
  } catch (e) {
    console.error('Failed to load category tree:', e)
  }
})
</script>

<style scoped>
@reference "../../assets/css/main.css";

.input {
  @apply w-full px-2 py-1 rounded border border-gray-300 bg-white text-gray-800 text-sm;
}

.input:focus {
  @apply outline-none ring-2 ring-blue-300;
}

.btn-sm {
  @apply inline-flex items-center px-2 py-1 text-xs rounded;
  background-color: var(--color-accent-purple);
  color: var(--color-bg-dark);
  border: 1px solid var(--color-accent-purple);
}

.btn-sm:hover {
  background-color: var(--color-accent-cyan);
  border-color: var(--color-accent-cyan);
}
</style>
