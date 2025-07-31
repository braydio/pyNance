<template>
  <div>
    <table class="min-w-full text-left text-sm">
      <thead>
        <tr>
          <th class="px-4 py-2">Date</th>
          <th class="px-4 py-2">Category</th>
          <th class="px-4 py-2">Description</th>
          <th class="px-4 py-2">Account</th>
          <th class="px-4 py-2 text-right">Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="tx in transactions" :key="tx.transaction_id">
          <td class="px-4 py-2">{{ formatDate(tx.date) }}</td>
          <td class="px-4 py-2">{{ tx.category_label || tx.category }}</td>
          <td class="px-4 py-2">{{ tx.description || '-' }}</td>
          <td class="px-4 py-2">{{ tx.account_name || tx.institution_name }}</td>
          <td class="px-4 py-2 text-right">
            {{ formatAmount(tx.amount) }}
          </td>
        </tr>
        <tr v-if="!transactions.length">
          <td class="px-4 py-2 italic text-center" colspan="5">No transactions found.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  transactions: { type: Array, default: () => [] }
});

function formatDate(date) {
  if (!date) return '-';
  return new Date(date).toLocaleDateString();
}

function formatAmount(amt) {
  if (amt == null) return '-';
  const n = Number(amt);
  return (n > 0 ? '+' : '') + n.toLocaleString(undefined, { minimumFractionDigits: 2 });
}
</script>

<style scoped>
table { width: 100%; }
th, td { border-bottom: 1px solid #eee; }
</style>

