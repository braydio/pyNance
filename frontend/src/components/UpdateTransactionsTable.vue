<template>
  <div class="transactions">
    <h3>Transactions</h3>
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Amount</th>
          <th>Description</th>
          <th>Category</th>
          <th>Merchant</th>
          <th>Account Name</th>
          <th>Institution</th>
          <th>Subtype</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(tx, index) in transactions" :key="tx.transaction_id">
          <!-- Date -->
          <td>
            <span v-if="!tx.isEditing">{{ tx.date || "N/A" }}</span>
            <input v-else type="date" v-model="tx.date" />
          </td>

          <!-- Amount -->
          <td>
            <span v-if="!tx.isEditing">{{ formatAmount(tx.amount) }}</span>
            <input
              v-else
              type="number"
              step="0.01"
              v-model.number="tx.amount"
            />
          </td>

          <!-- Description -->
          <td>
            <span v-if="!tx.isEditing">{{ tx.description || "N/A" }}</span>
            <input
              v-else
              type="text"
              v-model="tx.description"
            />
          </td>

          <!-- Category -->
          <td>
            <span v-if="!tx.isEditing">{{ tx.category || "Unknown" }}</span>
            <input
              v-else
              type="text"
              v-model="tx.category"
            />
          </td>

          <!-- Merchant Name -->
          <td>
            <span v-if="!tx.isEditing">{{ tx.merchant_name || "Unknown" }}</span>
            <input
              v-else
              type="text"
              v-model="tx.merchant_name"
            />
          </td>

          <!-- Account Name (read-only) -->
          <td>
            <span>{{ tx.account_name || "N/A" }}</span>
          </td>

          <!-- Institution Name (read-only) -->
          <td>
            <span>{{ tx.institution_name || "N/A" }}</span>
          </td>

          <!-- Subtype (read-only) -->
          <td>
            <span>{{ tx.subtype || "N/A" }}</span>
          </td>

          <!-- Actions -->
          <td>
            <button v-if="!tx.isEditing" @click="editTransaction(index)">Edit</button>
            <button v-if="!tx.isEditing" @click="markRecurring(index)">Mark as Recurring</button>
            <button v-if="tx.isEditing" @click="updateTransaction(index)">Save</button>
            <button v-if="tx.isEditing" @click="cancelEdit(index)">Cancel</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
import axios from "axios";
import api from "@/services/api";

export default {
  name: "TransactionsTable",
  props: {
    transactions: {
      type: Array,
      default: () => []
    },
  },
  methods: {
    formatAmount(amount) {
      const number = parseFloat(amount);
      const formatter = new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        currencySign: "accounting",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
      return formatter.format(number);
    },
    editTransaction(index) {
      const tx = this.transactions[index];
      tx._backup = { ...tx };
      tx.isEditing = true;
    },
    async updateTransaction(index) {
      const tx = this.transactions[index];
      try {
        const response = await axios.put("/api/transactions/update", tx);
        if (response.data.status === "success") {
          tx.isEditing = false;
          delete tx._backup;
        } else {
          console.error("Failed to update transaction:", response.data.message);
          alert("Failed to update transaction: " + response.data.message);
        }
      } catch (error) {
        console.error("Error updating transaction:", error);
        alert("Error updating transaction: " + error.message);
      }
    },
    cancelEdit(index) {
      const tx = this.transactions[index];
      // Restore the original backup if user cancels
      Object.assign(tx, tx._backup);
      delete tx._backup;
      tx.isEditing = false;
    },
    async markRecurring(index) {
      const tx = this.transactions[index];
      // Confirm with the user before marking as recurring
      if (!confirm("Mark this transaction as recurring?")) return;
      try {
        // Call the recurring endpoint for the account using the transaction's data.
        // We use the updateRecurringTransaction endpoint, which will update an existing recurring record or create a new one.
        const payload = {
          amount: tx.amount,
          description: tx.description
          // You could extend this payload to include frequency or other details if needed.
        };
        const response = await api.updateRecurringTransaction(tx.account_id, payload);
        if (response.status === "success") {
          alert("Transaction marked as recurring successfully.");
        } else {
          console.error("Failed to mark as recurring:", response.message);
          alert("Failed to mark as recurring: " + response.message);
        }
      } catch (error) {
        console.error("Error marking transaction as recurring:", error);
        alert("Error marking transaction as recurring: " + error.message);
      }
    },
  },
};
</script>b

<style scoped>
@import '@/styles/global-colors.css';

/* Base Styles */
body {
  margin: 0;
  padding: 0;
  font-family: \"Fira Code\", monospace;
  background-color: var(--color-bg-dark);
  color: var(--color-text-light);
}

/* Dashboard Layout */
.dashboard {
  padding: 1rem;
}

/* Header */
.dashboard-header {
  padding: 1rem;
  background-color: var(--color-bg-secondary);
  border-bottom: 2px solid var(--color-accent-yellow);
  margin-bottom: 1rem;
}
.dashboard-header h1 {
  margin: 0;
  color: var(--color-accent-yellow);
}
.dashboard-header h2 {
  margin-top: 0.5rem;
  color: var(--color-highlight);
}

/* Navigation Menu */
.menu {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
}
.menu button {
  padding: 0.5rem 1rem;
  background-color: var(--button-bg);
  border: none;
  border-radius: 4px;
  color: var(--color-text-light);
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.menu button:hover {
  background-color: var(--button-hover);
}

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
}

/* Charts Section */
.charts-section {
  display: flex;
  flex-direction: row;
  gap: 1rem;
  margin-bottom: 2rem;
  opacity: 0.85;
}
.charts-section > * {
  flex: 1 1 45%;
  height: 300px;
  background-color: var(--color-bg-secondary);
  padding: 0.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

/* Snapshot Section */
.snapshot-section {
  margin-top: 2rem;
}

/* Transactions Container */
.transactions-container {
  margin-top: 1rem;
}

/* Form Inputs */
.search-input {
  padding: 8px;
  width: 100%;
  max-width: 300px;
  margin-bottom: 10px;
  background-color: var(--color-bg-secondary);
  border: 2px groove var(--border-color);
  border-radius: 1px;
  color: var(--color-text-light);
}

/* Pagination Controls */
#pagination-controls {
  margin-top: 10px;
  text-align: center;
}
#pagination-controls button {
  padding: 4px 20px;
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: solid 4px;
  border-radius: 2px;
  border-color: var(--color-text-light);
  cursor: pointer;
  transition: background-color 0.3s ease;
}
#pagination-controls button:disabled {
  background-color: var(--button-disabled);
  cursor: not-allowed;
}
#pagination-controls button:hover:not(:disabled) {
  background-color: var(--button-hover);
}

/* Tables */
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid var(--border-color);
  padding: 8px;
  text-align: left;
}
th {
  background-color: var(--color-bg-secondary);
  cursor: pointer;
}
th:hover {
  background-color: var(--hover);
}

/* Transactions */
.transactions h3 {
  color: var(--color-accent-yellow);
}

.transactions table th {
  background-color: var(--color-bg-secondary);
  color: var(--color-text-light);
}

.transactions tbody tr:nth-child(odd) {
  background-color: var(--color-bg-dark);
}

.transactions tbody tr:hover {
  background-color: var(--hover);
}

.transactions button {
  background-color: var(--button-bg);
  color: var(--color-text-light);
  border: 1px solid var(--themed-border);
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.transactions button:hover {
  background-color: var(--button-hover);
  border-color: var(--color-accent-yellow);
}

/* Footer */
.dashboard-footer {
  text-align: center;
  margin-top: 2rem;
  padding: 1rem;
  font-size: 0.9rem;
  background-color: var(--color-bg-secondary);
  color: var(--footer-text);
}

</style>
