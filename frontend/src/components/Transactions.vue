<template>
    <div>
      <h1>Transactions</h1>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Name</th>
            <th>Category</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tx in transactions" :key="tx.id">
            <td>{{ tx.date }}</td>
            <td>{{ tx.amount }}</td>
            <td>{{ tx.name }}</td>
            <td>{{ tx.category }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  import axios from "axios";
  
  export default {
    name: "Transactions",
    data() {
      return {
        transactions: [],
      };
    },
    async created() {
      await this.fetchTransactions();
    },
    methods: {
      async fetchTransactions() {
        try {
          const response = await axios.get("/get_transactions");
          this.transactions = response.data.data.transactions;
        } catch (error) {
          console.error("Failed to fetch transactions:", error);
        }
      },
    },
  };
  </script>
  