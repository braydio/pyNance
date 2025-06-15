<template>
  <div class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md">
    <table class="min-w-full divide-y divide-[var(--divider)]">
      <thead>
        <tr>
          <th class="text-left">Institution</th>
          <th class="text-left">Provider</th>
          <th class="text-left">Last Refresh</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="inst in institutions" :key="inst.id">
          <tr class="cursor-pointer" @click="toggle(inst.id)">
            <td>{{ inst.name }}</td>
            <td>{{ inst.provider }}</td>
            <td>{{ formatDate(inst.last_refreshed) }}</td>
            <td>
              <button class="btn btn-sm" @click.stop="refresh(inst.id)">Refresh</button>
            </td>
          </tr>
          <tr v-if="expanded[inst.id]">
            <td colspan="4" class="p-0">
              <table class="w-full text-sm divide-y divide-[var(--divider)]">
                <thead>
                  <tr>
                    <th class="text-left">Account</th>
                    <th class="text-left">Type</th>
                    <th class="text-right">Balance</th>
                    <th class="text-left">Link</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="acc in inst.accounts" :key="acc.account_id">
                    <td>{{ acc.name }}</td>
                    <td>{{ acc.subtype || acc.type }}</td>
                    <td class="text-right">{{ formatBalance(acc.balance) }}</td>
                    <td>{{ acc.link_type }}</td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
import api from '@/services/api';
export default {
  name: 'InstitutionTable',
  data() {
    return { institutions: [], expanded: {}, loading: true };
  },
  methods: {
    toggle(id) {
      this.$set(this.expanded, id, !this.expanded[id]);
    },
    formatDate(d) {
      if (!d) return 'N/A';
      return new Date(d).toLocaleString();
    },
    formatBalance(b) {
      const num = parseFloat(b || 0);
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num);
    },
    async refresh(id) {
      await api.refreshInstitution(id);
      this.fetch();
    },
    async fetch() {
      const res = await api.getInstitutions();
      if (res.status === 'success') {
        this.institutions = res.institutions;
      }
      this.loading = false;
    }
  },
  mounted() {
    this.fetch();
  }
};
</script>

<style scoped>
th, td { @apply p-2; }
</style>
