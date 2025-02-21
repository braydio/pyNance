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
        </tr>
      </thead>
      <tbody>
        <tr v-for="tx in transactions" :key="tx.transaction_id">
          <td>{{ tx.date || "N/A" }}</td>
          <td>{{ formatAmount(tx.amount) }}</td>
          <td>{{ tx.description || "N/A" }}</td>
          <td>{{ tx.category || "Unknown" }}</td>
          <td>{{ tx.merchant_name || "Unknown" }}</td>
          <td>{{ tx.account_name || "N/A" }}</td>
          <td>{{ tx.institution_name || "N/A" }}</td>
          <td>{{ tx.subtype || "N/A" }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script>
export default {
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
</style>
