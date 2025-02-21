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
            <td>
              <span v-if="!tx.isEditing">{{ tx.date || "N/A" }}</span>
              <input v-else type="date" v-model="tx.date" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ formatAmount(tx.amount) }}</span>
              <input v-else type="number" step="0.01" v-model.number="tx.amount" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.description || "N/A" }}</span>
              <input v-else type="text" v-model="tx.description" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.category || "Unknown" }}</span>
              <input v-else type="text" v-model="tx.category" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.merchant_name || "Unknown" }}</span>
              <input v-else type="text" v-model="tx.merchant_name" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.account_name || "N/A" }}</span>
              <input v-else type="text" v-model="tx.account_name" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.institution_name || "N/A" }}</span>
              <input v-else type="text" v-model="tx.institution_name" />
            </td>
            <td>
              <span v-if="!tx.isEditing">{{ tx.subtype || "N/A" }}</span>
              <input v-else type="text" v-model="tx.subtype" />
            </td>
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
      transactions: Array,
      sortKey: String,
      sortOrder: Number,
    },
    methods: {
      formatAmount(amount) {
        // Format as accounting currency: negatives in parentheses
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
        // Make a backup of the original data
        tx._backup = { ...tx };
        tx.isEditing = true;
      },
      async updateTransaction(index) {
        const tx = this.transactions[index];
        try {
          // Assume our API endpoint accepts a PUT request to update a transaction.
          const response = await axios.put("/api/teller/update", tx);
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
        // Restore original values
        Object.assign(tx, tx._backup);
        delete tx._backup;
        tx.isEditing = false;
      },
    },
  };
  </script>
  
  <style scoped>
  .transactions {
    margin-top: 20px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th,
  td {
    border: 1px solid var(--border-color);
    padding: 8px;
    text-align: left;
  }
  th {
    background: var(--secondary-bg);
    cursor: pointer;
  }
  th:hover {
    background: var(--hover-bg);
  }
  button {
    padding: 4px 8px;
    margin-right: 4px;
    font-size: 0.8rem;
  }
  </style>
  