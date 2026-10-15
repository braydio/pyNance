<!-- Institutions.vue - Overview of linked institutions and accounts. -->
<template>
  <BasePageLayout>
    <PageHeader :icon="Landmark">
      <template #title>Institutions</template>
      <template #subtitle>Operator view of linked providers and accounts</template>
    </PageHeader>
    <section>
      <InstitutionTable />
    </section>
  </BasePageLayout>
</template>

<script setup>
// Basic institutions page showing existing InstitutionTable
// Advanced analytics and management features will be added incrementally.
import { Landmark } from 'lucide-vue-next'
import PageHeader from '@/components/ui/PageHeader.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
