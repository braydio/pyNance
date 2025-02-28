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
      // Format as accounting-style currency, e.g. negatives in parentheses
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
      // Keep a backup of original data in case user cancels
      tx._backup = { ...tx };
      tx.isEditing = true;
    },
    async updateTransaction(index) {
      const tx = this.transactions[index];
      try {
        // Example: your Teller endpoint for updating a transaction
        const response = await axios.put("/api/teller/transactions/update", tx);
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
  },
};
</script>

<style scoped>
/* Gruvbox-inspired palette (dark) */
:root {
  --gruvbox-bg: #282828;        /* Dark background */
  --gruvbox-fg: #ebdbb2;        /* Light text */
  --gruvbox-accent: #d65d0e;    /* Orange accent */
  --gruvbox-border: #3c3836;    /* Dark border */
  --gruvbox-hover: #b0520c;     /* Darker accent */
  --gruvbox-bg-hover: #32302f;  /* Hover row background */
}

.transactions {
  margin-top: 20px;
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-fg);
  padding: 1rem;
  border: 1px solid var(--gruvbox-border);
  border-radius: 4px;
}

.transactions h3 {
  margin-top: 0;
  color: var(--gruvbox-accent);
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 0.5rem;
}

/* Table Head */
thead {
  background-color: var(--gruvbox-border);
}
th {
  padding: 8px;
  text-align: left;
  background-color: var(--gruvbox-border);
  color: var(--gruvbox-fg);
}

/* Table Body */
tbody tr:nth-child(even) {
  background-color: var(--gruvbox-bg-hover);
}
td {
  border: 1px solid var(--gruvbox-border);
  padding: 8px;
  text-align: left;
}

/* Buttons */
button {
  background-color: var(--gruvbox-accent);
  color: var(--gruvbox-fg);
  border: 1px solid var(--gruvbox-accent);
  padding: 0.4rem 0.8rem;
  margin-right: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  border-radius: 3px;
  transition: background-color 0.2s, color 0.2s, border 0.2s;
}

button:hover {
  background-color: var(--gruvbox-bg);
  color: var(--gruvbox-accent);
}
</style>
