<!-- Institutions.vue - Overview of linked institutions and accounts. -->
<template>
  <AppLayout>
    <template #header>
      <BasePageLayout>
        <div class="text-center p-4 rounded-lg shadow-md bg-[var(--color-bg)]">
          <h1 class="text-3xl font-bold text-[var(--color-accent-cyan)]">Institutions</h1>
          <p class="text-sm text-muted">Overview of all linked providers and accounts</p>
        </div>
      </BasePageLayout>
    </template>
    <BasePageLayout>
      <section>
        <InstitutionTable />
      </section>
    </BasePageLayout>
  </AppLayout>
</template>

<script setup>
// Basic institutions page showing existing InstitutionTable
// Advanced analytics and management features will be added incrementally.
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import InstitutionTable from '@/components/tables/InstitutionTable.vue'
</script>

<style scoped>
@reference "../assets/css/main.css";
</style>
