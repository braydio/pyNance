<template>
  <div class="w-full bg-white shadow p-4 rounded-xl flex flex-col gap-6">
    <!-- Daily Net Income Chart -->
    <div>
      <h2 class="text-lg font-semibold mb-2">Daily Net Income</h2>
      <BarChart width="100%" height="300px" :data="netIncomeData">
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Bar dataKey="net" fill="#4ade80" @click="handleBarClick" />
      </BarChart>
    </div>

    ```
    <!-- Transactions Modal -->
    <Modal v-if="selectedDayTransactions.length" @close="selectedDayTransactions = []">
      <template #title>Transactions for {{ selectedDay }}</template>
      <template #body>
        <table class="w-full text-left">
          <thead>
            <tr>
              <th class="py-1 px-2">Date</th>
              <th class="py-1 px-2">Description</th>
              <th class="py-1 px-2">Amount</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(tx, idx) in selectedDayTransactions" :key="idx">
              <td class="py-1 px-2">{{ tx.date }}</td>
              <td class="py-1 px-2">{{ tx.description }}</td>
              <td class="py-1 px-2 text-right">${{ tx.amount.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </template>
    </Modal>
    ```

  </div>
</template>

<script setup>
import { ref } from 'vue';
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import Modal from '@/components/ui/Modal.vue';

const netIncomeData = [
  { date: '2025-05-01', net: 120 },
  { date: '2025-05-02', net: -40 },
  { date: '2025-05-03', net: 75 },
];

const transactionsMock = {
  '2025-05-01': [
    { date: '2025-05-01', description: 'Coffee', amount: -3.5 },
    { date: '2025-05-01', description: 'Salary', amount: 150 },
  ],
  '2025-05-02': [
    { date: '2025-05-02', description: 'Groceries', amount: -40 },
  ],
  '2025-05-03': [
    { date: '2025-05-03', description: 'Bonus', amount: 75 },
  ],
};

const selectedDayTransactions = ref([]);
const selectedDay = ref('');

function handleBarClick(data) {
  const date = data?.activeLabel;
  if (selectedDay.value === date) {
    selectedDayTransactions.value = [];
    selectedDay.value = '';
  } else {
    selectedDayTransactions.value = transactionsMock[date] || [];
    selectedDay.value = date;
  }
}
</script>

<style scoped>
table {
  border-collapse: collapse;
}

th,
td {
  border-bottom: 1px solid #ddd;
}
</style>
