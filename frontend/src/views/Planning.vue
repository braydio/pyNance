<template>
  <BasePageLayout>
    <PageHeader>
      <template #icon>
        <Calendar class="w-6 h-6" />
      </template>
      <template #title>Planning</template>
      <template #subtitle>Manage your budgeting and allocations</template>
    </PageHeader>
    <pre>{{ JSON.stringify(state, null, 2) }}</pre>
  </BasePageLayout>
</template>

<script setup>
import { usePlanning } from '@/composables/usePlanning'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { Calendar } from 'lucide-vue-next'

/**
 * Top-level view for budgeting and allocation planning.
 * Currently displays the raw planning state as a scaffold.
 */
const { state } = usePlanning()
</script>
