<template>
    <div class="transactions">
      <h3>Transactions</h3>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Amount</th>
            <th>Name</th>
            <th>Category</th>
            <th>Merchant</th>
            <th>Account</th>
            <th>Institution</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tx in transactions" :key="tx.id">
            <td>{{ tx.date || "N/A" }}</td>
            <td>{{ tx.amount || "N/A" }}</td>
            <td>{{ tx.name || "N/A" }}</td>
            <td>{{ tx.category || "Uncategorized" }}</td>
            <td>{{ tx.merchant_name || "Unknown" }}</td>
            <td>{{ tx.account_name || "Unknown Account" }}</td>
            <td>{{ tx.institution_name || "Unknown Institution" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      transactions: Array,
    },
  };
  </script>
  
  <style scoped>
  .transactions {
    margin: 20px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
  }
  th, td {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
  }
  </style>
  