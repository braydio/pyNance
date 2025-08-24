<template>
  <BasePageLayout>
    <template #header>
      <PageHeader title="Institutions" subtitle="Overview of all linked providers and accounts" />
    </template>
    <InstitutionTable />
  </BasePageLayout>
</template>

<script setup>
// Basic institutions page showing existing InstitutionTable
// Advanced analytics and management features will be added incrementally.
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
