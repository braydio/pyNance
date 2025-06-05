<template>
  <div class="transactions space-y-4 p-6 bg-gray-50 rounded-xl shadow">
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
    <table class="min-w-full divide-y divide-gray-200 mt-4">
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
          v-for="(tx, index) in filteredTransactions"
          :key="tx.transaction_id"
          :class="['text-sm', editingIndex === index ? 'bg-yellow-100' : 'hover:bg-gray-100']"
        >
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

    <!-- Empty State -->
    <div v-if="filteredTransactions.length === 0" class="text-center text-gray-500">
      No transactions found.
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()
const emit = defineEmits(['editRecurringFromTransaction'])
const props = defineProps({ transactions: Array })

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

async function saveEdit(tx) {
  try {
    await axios.put('/api/transactions/update', {
      transaction_id: tx.transaction_id,
      ...editBuffer.value,
    })
    Object.assign(tx, editBuffer.value)
    editingIndex.value = null
    toast.success('Transaction updated')

    const confirmed = confirm(
      `Always use description "${editBuffer.value.description}" for merchant "${tx.merchant_name}" on account "${tx.account_name}"?`,
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

function formatAmount(amount) {
  const number = parseFloat(amount)
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    currencySign: 'accounting',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return formatter.format(number)
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
.input {
  @apply w-full px-2 py-1 rounded border border-gray-300 bg-white text-gray-800 text-sm;
}

.input:focus {
  @apply outline-none ring-2 ring-blue-300;
}

.btn-sm {
  @apply inline-flex items-center px-2 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700;
}
</style>
