<template>
  <div class="p-6 space-y-6">
    <h1 class="text-2xl font-bold">Recurring Scan Demo</h1>
    <ScanResultsModal :results="scanResults" />
    <ScanResultsTable :results="scanResults" />
    <ScanResultsList :results="scanResults" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { scanRecurringTransactions } from '@/api/recurring';
import ScanResultsModal from '@/components/recurring/ScanResultsModal.vue';
import ScanResultsTable from '@/components/recurring/ScanResultsTable.vue';
import ScanResultsList from '@/components/recurring/ScanResultsList.vue';

const route = useRoute();
const accountId = route.params.accountId || '1';
const scanResults = ref([]);

onMounted(async () => {
  try {
    const data = await scanRecurringTransactions(accountId);
    scanResults.value = data.actions || [];
  } catch (err) {
    console.error('Failed to load scan results', err);
  }
});
</script>
