<template>
  <BasePageLayout>
    <PageHeader :icon="Activity">
      <template #title>R/S Arbitrage Monitor</template>
      <template #subtitle>Live R/S arbitrage feed</template>
    </PageHeader>
    <pre
      v-if="content"
      class="bg-gray-800 text-white p-4 rounded whitespace-pre-wrap"
    >{{ content }}</pre>
    <div v-else>Loading...</div>
  </BasePageLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchArbitrageData } from '@/api/arbitrage'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { Activity } from 'lucide-vue-next'

const content = ref('')

const load = async () => {
  try {
    const data = await fetchArbitrageData()
    content.value = data.content || JSON.stringify(data, null, 2)
  } catch (err) {
    console.error('Failed to load arbitrage data', err)
  }
}

onMounted(() => {
  load()
  setInterval(load, 5000)
})
</script>
