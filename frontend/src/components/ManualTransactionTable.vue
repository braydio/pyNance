<template>
  <div class="mt-6">
    <Card>
      <CardContent>
        <h2 class="text-lg font-bold mb-4">📝 Manually Imported Transactions</h2>

        <div v-if="loading" class="text-gray-500">Loading manual transactions...</div>

        <table v-else class="w-full text-sm border border-gray-300">
          <thead>
            <tr class="bg-gray-100">
              <th class="text-left p-2">Date</th>
              <th class="text-left p-2">Description</th>
              <th class="text-left p-2">Amount</th>
              <th class="text-left p-2">Account</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="txn in manualTransactions" :key="txn.transaction_id">
              <td class="p-2">{{ txn.date }}</td>
              <td class="p-2">{{ txn.name }}</td>
              <td class="p-2">{{ formatCurrency(txn.amount) }}</td>
              <td class="p-2">{{ txn.account_name || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Card, CardContent } from '@/components/ui/card';
import axios from 'axios';

const manualTransactions = ref([]);
const loading = ref(true);

const fetchManualTransactions = async () => {
  try {
    const res = await axios.get('/api/transactions/manual');
    manualTransactions.value = res.data;
  } catch (err) {
    console.error('Failed to fetch manual transactions', err);
  } finally {
    loading.value = false;
  }
};

const formatCurrency = (amount) => `$${Number(amount).toFixed(2)}`;

onMounted(() => {
  fetchManualTransactions();
});
</script>

<style scoped>
th, td {
  border-bottom: 1px solid #ddd;
}
</style>
