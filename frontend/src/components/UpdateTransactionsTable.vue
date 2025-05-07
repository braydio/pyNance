/ * UpdateTransactionsTable.vue  -- DEV Note: Look to integrate in the same module
as TransactionsTable.vue, cut down on duplicated code.
Flag the version of the table in the Transactions page as the
version that can edit transactions elements.* /
<template>
  <div class="transactions">
    <div class="actions-row">
      <h3>Transactions</h3>
      <button class="export-btn" @click="exportTransactions">Export CSV</button>
    </div>

    <div class="filter-row">
      <select v-model="selectedPrimaryCategory" @change="onPrimaryCategoryChange" class="filter-input">
        <option value="">All Categories</option>
        <option v-for="group in categoryTree" :key="group.name" :value="group.name">
          {{ group.name }}
        </option>
      </select>

      <select v-model="selectedSubcategory" class="filter-input" :disabled="!subcategoryOptions.length">
        <option value="">All Subcategories</option>
        <option v-for="child in subcategoryOptions" :key="child.id" :value="child.name">
          {{ child.name }}
        </option>
      </select>
    </div>

    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Amount</th>
          <th>Description</th>
          <th>Category</th>
          <th>Merchant</th>
          <th>Account</th>
          <th>Institution</th>
          <th>Subtype</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(tx, index) in filteredTransactions" :key="tx.transaction_id">
          <td>{{ formatDate(tx.date) }}</td>
          <td>{{ formatAmount(tx.amount) }}</td>
          <td>{{ tx.description || 'N/A' }}</td>
          <td>{{ tx.category || 'Unknown' }}</td>
          <td>{{ tx.merchant_name || 'N/A' }}</td>
          <td>{{ tx.account_name || 'N/A' }}</td>
          <td>{{ tx.institution_name || 'N/A' }}</td>
          <td>{{ tx.subtype || 'N/A' }}</td>
          <td>
            <button class="btn btn-sm" @click="editTransaction(index)">Edit</button>
            <button class="btn btn-sm" @click="markRecurring(index)">Mark</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  transactions: Array
})

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

function onPrimaryCategoryChange() {
  selectedSubcategory.value = ''
}

function editTransaction(index) {
  console.log('Edit clicked for:', props.transactions[index])
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

th,
td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--divider);
}

tbody tr:hover {
  background-color: var(--color-hover-light);
}
</style>
