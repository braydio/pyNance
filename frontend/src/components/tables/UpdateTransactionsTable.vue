<template>
  <div class="transactions">
    <VueToast v-if="toast.message" :type="toast.type" :message="toast.message" @close="toast.message = ''" />

    <table>
      <thead>
        <tr>
          <th @click="sortBy('date')">Date</th>
          <th @click="sortBy('amount')">Amount</th>
          <th @click="sortBy('description')">Description</th>
          <th @click="sortBy('category')">Category</th>
          <th @click="sortBy('merchant_name')">Merchant</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(tx, index) in filteredTransactions" :key="tx.transaction_id"
          :class="{ 'editing-row': editingIndex === index }">
          <td>
            <input v-if="editingIndex === index" v-model="editBuffer.date" type="date" />
            <span v-else>{{ formatDate(tx.date) }}</span>
          </td>

          <td>
            <input v-if="editingIndex === index" v-model.number="editBuffer.amount" type="number" step="0.01"
              placeholder="0.00" />
            <span v-else>{{ formatAmount(tx.amount) }}</span>
          </td>

          <td>
            <input v-if="editingIndex === index" v-model="editBuffer.description" type="text"
              placeholder="Description" />
            <span v-else>{{ tx.description }}</span>
          </td>

          <td>
            <select v-if="editingIndex === index" v-model="editBuffer.category">
              <option disabled value="">-- Select Category --</option>
              <optgroup v-for="group in categoryTree" :label="group.name" :key="group.name">
                <option v-for="child in group.children" :key="child.id" :value="child.name">
                  {{ child.name }}
                </option>
              </optgroup>
            </select>
            <span v-else>{{ tx.category }}</span>
          </td>

          <td>
            <input v-if="editingIndex === index" v-model="editBuffer.merchant_name" type="text"
              placeholder="Merchant" />
            <span v-else>{{ tx.merchant_name }}</span>
          </td>

          <td>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import VueToast from '@/components/base/Toast.vue'

const emit = defineEmits(['editRecurringFromTransaction'])
const props = defineProps({ transactions: Array })

const editingIndex = ref(null)
const editBuffer = ref({ amount: 0, description: '', date: '', merchant_name: '', category: '' })
const toast = ref({ type: '', message: '' })

const sortKey = ref('date')
sortKey.value = 'date'
const sortOrder = ref('desc')

function startEdit(index, tx) {
  editingIndex.value = index
  editBuffer.value.amount = tx.amount
  editBuffer.value.description = tx.description
  editBuffer.value.date = tx.date
  editBuffer.value.merchant_name = tx.merchant_name || ''
  editBuffer.value.category = tx.category || ''
}

function cancelEdit() {
  editingIndex.value = null
  editBuffer.value = { amount: 0, description: '', date: '', merchant_name: '', category: '' }
}

async function saveEdit(tx) {
  try {
    await axios.put('/api/transactions/update', {
      transaction_id: tx.transaction_id,
      amount: parseFloat(editBuffer.value.amount),
      description: editBuffer.value.description,
      date: editBuffer.value.date,
      merchant_name: editBuffer.value.merchant_name,
      category: editBuffer.value.category
    })
    toast.value = { type: 'success', message: 'Transaction updated successfully.' }

    const confirmed = confirm(
      `Always use description "${editBuffer.value.description}" for merchant "${tx.merchant_name}" on account "${tx.account_name}"?`
    )
    if (confirmed) {
      console.log('[RuleEngine] Create rule: if merchant is', tx.merchant_name)
    }
    editingIndex.value = null
  } catch (e) {
    console.error('Failed to save edit:', e)
    toast.value = { type: 'error', message: 'Failed to update transaction.' }
  }
}

function sortBy(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const categoryTree = ref([])
const selectedPrimaryCategory = ref('')
const selectedSubcategory = ref('')

const subcategoryOptions = computed(() => {
  const group = categoryTree.value.find(g => g.name === selectedPrimaryCategory.value)
  return group ? group.children : []
})

const filteredTransactions = computed(() => {
  let txs = [...props.transactions]
  if (selectedSubcategory.value) {
    txs = txs.filter(tx =>
      tx.category?.toLowerCase().includes(selectedSubcategory.value.toLowerCase())
    )
  }
  txs.sort((a, b) => {
    const aVal = a[sortKey.value] || ''
    const bVal = b[sortKey.value] || ''
    return (sortOrder.value === 'asc' ? 1 : -1) * (aVal > bVal ? 1 : aVal < bVal ? -1 : 0)
  })
  return txs
})

const formatDate = (str) => {
  if (!str) return 'N/A'
  return new Date(str).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

const formatAmount = (amt) => {
  const n = parseFloat(amt)
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(n)
}

function exportTransactions() {
  window.open('/api/export/transactions', '_blank')
}

function markRecurring(index) {
  console.log('Mark recurring for:', props.transactions[index])
}

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
.transactions {
  background: var(--color-bg-secondary);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 2px 12px var(--shadow);
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.export-btn {
  background-color: transparent;
  color: var(--neon-purple);
  border: 1px solid var(--neon-purple);
  border-radius: 2rem;
  padding: 0.35rem 0.9rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.export-btn:hover {
  background-color: var(--neon-purple);
  color: var(--color-bg-dark);
  border-color: var(--neon-purple);
}

.filter-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-input {
  padding: 0.4rem 0.9rem;
  border-radius: 2rem;
  border: 2px solid var(--neon-purple);
  background-color: transparent;
  color: var(--neon-purple);
  font-size: 0.9rem;
  transition: all 0.2s ease-in-out;
}

.filter-input:hover,
.filter-input:focus {
  background-color: var(--neon-purple);
  color: var(--color-bg-dark);
  outline: none;
}

th {
  background-color: var(--color-bg-darkest);
  color: var(--color-accent);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  user-select: none;
}

th:hover {
  background-color: var(--color-hover-light);
}

th.sorted-asc::after {
  content: ' \25B2';
}

th.sorted-desc::after {
  content: ' \25BC';
}

th,
td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--divider);
}

tbody tr:hover {
  background-color: var(--color-hover-light);
}

/* Highlight row in edit mode */
tbody tr.editing-row {
  background-color: var(--color-bg-highlight);
  box-shadow: inset 0 0 0 2px var(--color-accent);
}

/* Style editable input fields */
td input,
td select {
  width: 100%;
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--divider);
  border-radius: 6px;
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
  font-family: inherit;
  font-size: 0.9rem;
}

td input[type="date"] {
  font-family: var(--font-sans);
  text-transform: none;
}

td input:focus,
td select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-fade);
}

.btn-sm {
  font-size: 0.8rem;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  margin-right: 0.25rem;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: 1px solid var(--divider);
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-sm:hover {
  background-color: var(--button-hover-bg);
}
</style>
