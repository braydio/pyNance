<template>
  <BasePageLayout>
    <PageHeader>
      <template #icon>
        <Repeat class="w-6 h-6" />
      </template>
      <template #title>Recurring Scan Demo</template>
      <template #subtitle>Demo results for recurring transaction scan</template>
    </PageHeader>
    <ScanResultsModal :results="scanResults" />
    <ScanResultsTable :results="scanResults" />
    <ScanResultsList :results="scanResults" />
  </BasePageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { scanRecurringTransactions } from '@/api/recurring'
import ScanResultsModal from '@/components/recurring/ScanResultsModal.vue'
import ScanResultsTable from '@/components/recurring/ScanResultsTable.vue'
import ScanResultsList from '@/components/recurring/ScanResultsList.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { Repeat } from 'lucide-vue-next'

const route = useRoute()
const accountId = route.params.accountId || '1'
const scanResults = ref([])

onMounted(async () => {
  try {
    const data = await scanRecurringTransactions(accountId)
    scanResults.value = data.actions || []
  } catch (err) {
    console.error('Failed to load scan results', err)
  }
})
</script>
