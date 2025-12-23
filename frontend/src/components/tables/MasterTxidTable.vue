<template>
  <div class="transactions space-y-4 p-6 bg-gray-50 rounded-xl shadow">
    <!-- Filter Row -->
    <div class="flex gap-4 items-center text-sm text-gray-700">
      <div>
        <label class="block mb-1 font-medium">Category Group</label>
        <select v-model="selectedPrimaryCategory" class="input">
          <option value="">-- All Categories --</option>
          <option v-for="group in categoryTree" :key="group.name" :value="group.name">
            {{ group.name }}
          </option>
        </select>
      </div>

      <div>
        <label class="block mb-1 font-medium">Subcategory</label>
        <select v-model="selectedSubcategory" class="input" :disabled="!selectedPrimaryCategory">
          <option value="">-- All Subcategories --</option>
          <option v-for="sub in subcategoryOptions" :key="sub.id" :value="sub.name">
            {{ sub.name }}
          </option>
        </select>
      </div>
    </div>
    <div v-if="activeFilterTags.length" class="filter-tags">
      <span v-for="filter in activeFilterTags" :key="filter.key" class="filter-tag">
        <span class="filter-tag__label">{{ filter.label }}:</span>
        <span class="filter-tag__value">{{ filter.value }}</span>
        <button type="button" class="filter-tag__remove" @click="removeFilterTag(filter.key)">
          ×
        </button>
      </span>
    </div>
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-100 text-gray-700 text-sm font-semibold uppercase">
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
          <th class="px-3 py-2">Account</th>
          <th class="px-3 py-2">Institution</th>
          <th class="px-3 py-2">Subtype</th>
          <th class="px-3 py-2">Actions</th>
        </tr>
      </thead>

      <tbody>
        <tr v-for="tx in paginatedTransactions" :key="tx.transaction_id">
          :class="['text-sm', editingIndex === index ? 'bg-yellow-100' : 'hover:bg-gray-100']">
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
              <button class="btn-sm" @click="markRecurring(index)">Mark</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="filteredTransactions.length === 0" class="text-gray-500 text-sm">
      No transactions found.
    </div>
  </div>
</template>

<script setup>
/**
 * MasterTxidTable.vue
 *
 * Editable transactions table with stacked category filters and tag summaries.
 */
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { updateTransaction } from '@/api/transactions'
import { useToast } from 'vue-toastification'
import { formatAmount } from '@/utils/format'

const toast = useToast()
const emit = defineEmits(['editRecurringFromTransaction'])
const props = defineProps({ transactions: Array })

const selectedPrimaryCategory = ref('')
const selectedSubcategory = ref('')

const subcategoryOptions = computed(() => {
  const group = categoryTree.value.find((g) => g.name === selectedPrimaryCategory.value)
  return group ? group.children : []
})

const editingIndex = ref(null)
const editBuffer = ref({
  date: '',
  amount: null,
  description: '',
  category: '',
  merchant_name: '',
})

const categoryTree = ref([])
const sortKey = ref('date')
const sortOrder = ref('asc')

const activeFilterTags = computed(() => {
  const tags = []
  if (selectedPrimaryCategory.value) {
    tags.push({ key: 'primary', label: 'Category', value: selectedPrimaryCategory.value })
  }
  if (selectedSubcategory.value) {
    tags.push({ key: 'subcategory', label: 'Subcategory', value: selectedSubcategory.value })
  }
  return tags
})

/**
 * Remove a selected filter tag.
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
  }
}

/**
 * Resolve the primary category name for a transaction.
 * @param {Object} tx - Transaction record.
 * @returns {string} Primary category label if available.
 */
function getPrimaryCategory(tx) {
  if (tx.primary_category) {
    return String(tx.primary_category)
  }
  if (tx.category && typeof tx.category === 'string') {
    return tx.category.split(':')[0].trim()
  }
  return ''
}

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

async function saveEdit(tx) {
  try {
    await updateTransaction({
      transaction_id: tx.transaction_id,
      ...editBuffer.value,
    })
    Object.assign(tx, editBuffer.value)
    editingIndex.value = null
    toast.success('Transaction updated')

    const confirmed = confirm(
      [
        `Always use description "${editBuffer.value.description}" for merchant "${tx.merchant_name}"`,
        `on account "${tx.account_name}"?`,
      ].join(' '),
    )
    if (confirmed) {
      console.log('[RuleEngine] Create rule: if merchant is', tx.merchant_name)
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

const filteredTransactions = computed(() => {
  let txs = [...props.transactions]

  if (selectedPrimaryCategory.value) {
    const primary = selectedPrimaryCategory.value.toLowerCase()
    txs = txs.filter((tx) => getPrimaryCategory(tx).toLowerCase() === primary)
  }

  if (selectedSubcategory.value) {
    txs = txs.filter((tx) =>
      tx.category?.toLowerCase().includes(selectedSubcategory.value.toLowerCase()),
    )
  }

  txs.sort((a, b) => {
    const aVal = a[sortKey.value] || ''
    const bVal = b[sortKey.value] || ''
    return (sortOrder.value === 'asc' ? 1 : -1) * (aVal > bVal ? 1 : aVal < bVal ? -1 : 0)
  })

  return txs
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
  @apply inline-flex items-center px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700;
}

.filter-tags {
  @apply flex flex-wrap items-center gap-2 text-sm;
}

.filter-tag {
  @apply inline-flex items-center gap-2 rounded-full border border-gray-300 bg-white px-3 py-1 text-xs text-gray-700;
}

.filter-tag__label {
  @apply uppercase tracking-wide text-[11px] text-gray-500;
}

.filter-tag__value {
  @apply font-semibold text-gray-800;
}

.filter-tag__remove {
  @apply text-gray-500 hover:text-gray-800 transition;
}
</style>
