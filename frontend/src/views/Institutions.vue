<!--
  Institutions.vue
  Overview of linked providers and accounts.
-->
<template>
  <AppLayout>
    <BasePageLayout>
      <template #header>
        <PageHeader
          title="Institutions"
          subtitle="Overview of all linked providers and accounts"
          :icon="Building"
        />
      </template>
      <section>
        <InstitutionTable />
      </section>
    </BasePageLayout>
  </AppLayout>
</template>

<script setup>
// Basic institutions page showing existing InstitutionTable
// Advanced analytics and management features will be added incrementally.
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import { Building } from 'lucide-vue-next'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
