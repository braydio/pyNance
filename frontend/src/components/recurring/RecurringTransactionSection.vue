<!--
  RecurringTransactionSection.vue
  -------------------------------
  Manage user-defined recurring transaction rules and trigger scans for
  auto-detected reminders.
-->

<template>
  <section id="recurring" class="recurring-manager">
    <h2 class="heading-md mb-4">Recurring Transactions</h2>
    <!-- Form Modal Toggle -->
    <button @click="resetForm" class="btn">+ Add Recurring Transaction Rule</button>
    <button @click="scanForRecurring" class="btn">Scan for Recurring</button>
    <!-- Form -->
    <div v-if="showForm" class="recurring-form">
      <input v-model="transactionId" placeholder="Transaction ID (e.g. tx_abc123)" />
      <input v-model="description" placeholder="Description (optional)" />
      <input v-model.number="amount" type="number" step="0.01" placeholder="Amount ($)" />
      <select v-model="frequency">
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
        <option value="yearly">Yearly</option>
      </select>
      <input v-model="nextDueDate" type="date" placeholder="Next Due Date" />
      <input v-model="notes" placeholder="Notes" />
      <button @click="saveRecurring" :disabled="loading">
        {{ loading ? 'Saving...' : isEditing ? 'Update' : 'Save' }}
      </button>
    </div>

    <!-- User-Defined Rules Table -->
    <div class="table-section mt-6" v-if="userRules.length">
      <h3 class="subheading">Your Recurring Rules</h3>
      <table>
        <thead>
          <tr>
            <th>Description</th>
            <th>Frequency</th>
            <th>Next Due</th>
            <th>Amount</th>
            <th>Notes</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in userRules" :key="rule.description">
            <td>{{ rule.description }}</td>
            <td>{{ rule.frequency }}</td>
            <td>{{ rule.next_due_date }}</td>
            <td>{{ formatAmount(rule.amount) }}</td>
            <td>{{ rule.notes }}</td>
            <td>
              <button class="btn-sm" @click="editRule(rule)">Edit</button>
              <button class="btn-sm" @click="deleteRule(rule)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Auto Reminders -->
    <div class="auto-section mt-6" v-if="autoReminders.length">
      <h3 class="subheading">Detected Reminders</h3>
      <ul>
        <li v-for="(reminder, i) in autoReminders" :key="i" class="note">
          {{ reminder.description }} (${{ reminder.amount.toFixed(2) }}) due on
          {{ reminder.next_due_date }}
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scanRecurringTransactions } from '@/api/recurring'
import axios from 'axios'
import { formatAmount } from "@/utils/format"

const route = useRoute()
const accountId = route.params.accountId || '1'

const transactionId = ref('')
const description = ref('')
const amount = ref(0.0)
const frequency = ref('monthly')
const nextDueDate = ref('')
const notes = ref('')
const loading = ref(false)
const userRules = ref([])
const autoReminders = ref([])
const showForm = ref(false)
const isEditing = ref(false)

function resetForm() {
  transactionId.value = ''
  description.value = ''
  amount.value = 0
  frequency.value = 'monthly'
  nextDueDate.value = ''
  notes.value = ''
  isEditing.value = false
  showForm.value = true
}

function editRule(rule) {
  transactionId.value = rule.transaction_id || ''
  description.value = rule.description
  amount.value = rule.amount
  frequency.value = rule.frequency
  nextDueDate.value = rule.next_due_date
  notes.value = rule.notes
  isEditing.value = true
  showForm.value = true
}

/**
 * Remove a recurring rule from the backend and update local state.
 */
async function deleteRule(rule) {
  try {
    await axios.delete(`/api/recurring/accounts/${accountId}/recurringTx`, { data: rule })
    userRules.value = userRules.value.filter(
      (r) => r.description !== rule.description || r.amount !== rule.amount,
    )
  } catch (err) {
    console.error('Failed to delete rule:', err)
  }
}

/**
 * Trigger backend scan for recurring transactions and refresh reminders.
 */
async function scanForRecurring() {
  try {
    const res = await scanRecurringTransactions(accountId)
    if (Array.isArray(res?.reminders)) {
      userRules.value = res.reminders.filter((r) => r.source === 'user')
      autoReminders.value = res.reminders.filter((r) => r.source === 'auto')
    }
  } catch (err) {
    console.error('Failed to scan recurring transactions:', err)
  }
}

/**
 * Persist a recurring rule and update the list on success.
 */
async function saveRecurring() {
  if (!transactionId.value) return
  loading.value = true
  try {
    const payload = {
      description: description.value,
      amount: amount.value,
      frequency: frequency.value,
      next_due_date: nextDueDate.value,
      notes: notes.value || description.value || 'Untitled Recurring',
    }
    await axios.put(`/api/recurring/accounts/${accountId}/recurringTx`, payload)
    userRules.value = userRules.value.filter(
      (r) => r.description !== payload.description || r.amount !== payload.amount,
    )
    userRules.value.push(payload)
    resetForm()
  } catch (err) {
    console.error('Error saving recurring:', err)
  } finally {
    loading.value = false
  }
}

// Load existing reminders when the component mounts.
onMounted(async () => {
  try {
    const res = await axios.get(`/api/recurring/${accountId}/recurring`)
    if (Array.isArray(res.data?.reminders)) {
      userRules.value = res.data.reminders.filter((r) => r.source === 'user')
      autoReminders.value = res.data.reminders.filter((r) => r.source === 'auto')
    }
  } catch (err) {
    console.error('Failed to load recurring reminders:', err)
  }
})
</script>

<style scoped>
@reference "../../assets/css/main.css";

.recurring-manager {
  width: 100%;
  margin-top: 2rem;
  padding: 2rem;
  background-color: var(--color-bg-secondary);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.heading-md {
  font-size: 1.6rem;
  font-weight: bold;
  color: var(--color-accent-yellow);
  margin-bottom: 1rem;
}

.subheading {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--color-text-muted);
  margin-bottom: 0.75rem;
}

.recurring-form {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1.25rem;
}

.recurring-form input,
.recurring-form select {
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--divider);
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
}

.btn {
  grid-column: 1 / -1;
  justify-self: start;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: solid 2px var(--color-text-light);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

.btn:hover {
  background-color: var(--color-accent-purple);
  color: var(--button-bg);
  border: solid 2px var(--color-accent-purple);
}

.recurring-form button {
  grid-column: 1 / -1;
  justify-self: start;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: solid 2px var(--color-text-light);
  padding: 0.25rem 1.5rem;
  border-radius: 3px;
  cursor: pointer;
}

.recurring-form button:hover {
  background-color: var(--color-accent-purple);
  color: var(--button-bg);
  border: solid 2px var(--color-accent-purple);
}

.table-section table {
  width: 100%;
  background-color: var(--color-bg-dark);
  border-collapse: collapse;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 1rem;
}

table th,
table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--divider);
  text-align: left;
}

.note {
  font-size: 0.95rem;
  margin: 0.3rem 0;
  color: var(--color-accent);
}

.btn-sm {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.1rem;
}
</style>
