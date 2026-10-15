<template>
  <div class="p-4 bg-[var(--color-bg-secondary)] rounded-lg shadow-md institution-table">
    <p v-if="loading" class="text-sm text-muted" role="status">Loading institutions…</p>
    <div v-else-if="loadError" role="alert" class="text-sm">
      <p class="text-negative">Unable to load institutions.</p>
      <button type="button" class="btn btn-sm" @click="fetch">Retry</button>
    </div>
    <p v-else-if="!institutions.length" class="text-sm text-muted">No institutions linked yet.</p>
    <div v-else class="institution-scroll">
      <table class="min-w-full divide-y divide-[var(--divider)]">
        <thead>
          <tr>
            <th class="text-left" scope="col">Institution</th>
            <th class="text-left" scope="col">Provider</th>
            <th class="text-left" scope="col">Last Refresh</th>
            <th scope="col"><span class="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="inst in institutions" :key="inst.id">
            <tr>
              <td>
                <button
                  type="button"
                  class="expand-btn"
                  :aria-expanded="expanded[inst.id] ? 'true' : 'false'"
                  :aria-controls="`institution-panel-${inst.id}`"
                  :data-testid="`institution-toggle-${inst.id}`"
                  @click="toggle(inst.id)"
                >
                  <span aria-hidden="true">{{ expanded[inst.id] ? '▾' : '▸' }}</span>
                  {{ inst.name }}
                </button>
              </td>
              <td>{{ inst.provider }}</td>
              <td>{{ formatDate(inst.last_refreshed) }}</td>
              <td>
                <button
                  type="button"
                  class="btn btn-sm"
                  :disabled="refreshing[inst.id]"
                  :aria-label="`Refresh ${inst.name}`"
                  :data-testid="`institution-refresh-${inst.id}`"
                  @click.stop="refresh(inst.id)"
                >
                  {{ refreshing[inst.id] ? 'Refreshing…' : 'Refresh' }}
                </button>
                <p
                  v-if="refreshErrors[inst.id]"
                  class="text-sm text-negative"
                  role="alert"
                  :data-testid="`institution-refresh-error-${inst.id}`"
                >
                  {{ refreshErrors[inst.id] }}
                </p>
              </td>
            </tr>
            <tr v-if="expanded[inst.id]">
              <td colspan="4" class="p-0">
                <div :id="`institution-panel-${inst.id}`" class="nested-scroll">
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
                        <td class="wrap-anywhere">{{ acc.name }}</td>
                        <td>{{ acc.subtype || acc.type }}</td>
                        <td class="text-right tabular-currency">
                          {{ formatBalance(acc.balance) }}
                        </td>
                        <td>{{ acc.link_type }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import api from '@/services/api'
export default {
  name: 'InstitutionTable',
  data() {
    return {
      institutions: [],
      expanded: {},
      loading: true,
      loadError: false,
      refreshing: {},
      refreshErrors: {},
    }
  },
  methods: {
    /**
     * Toggle expansion state for a given institution row.
     * @param {number|string} id - Institution identifier.
     */
    toggle(id) {
      this.expanded[id] = !this.expanded[id]
    },
    formatDate(d) {
      if (!d) return 'N/A'
      return new Date(d).toLocaleString()
    },
    formatBalance(b) {
      const num = parseFloat(b || 0)
      return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num)
    },
    async refresh(id) {
      if (this.refreshing[id]) return
      this.refreshing = { ...this.refreshing, [id]: true }
      this.refreshErrors = { ...this.refreshErrors, [id]: '' }
      try {
        await api.refreshInstitution(id)
        await this.fetch()
      } catch (error) {
        this.refreshErrors = {
          ...this.refreshErrors,
          [id]: error?.message ? `Refresh failed: ${error.message}` : 'Refresh failed. Try again.',
        }
      } finally {
        this.refreshing = { ...this.refreshing, [id]: false }
      }
    },
    async fetch() {
      this.loadError = false
      try {
        const res = await api.getInstitutions()
        if (res.status === 'success') {
          this.institutions = res.institutions
        } else {
          this.loadError = this.institutions.length === 0
        }
      } catch {
        this.loadError = this.institutions.length === 0
      } finally {
        this.loading = false
      }
    },
  },
  mounted() {
    this.fetch()
  },
}
</script>

<style scoped>
@reference "../../assets/css/main.css";
th,
td {
  @apply p-2;
}

/* position: relative keeps absolutely positioned helpers (e.g. .sr-only) inside the region
   instead of letting them extend the document's scrollable width. */
.institution-scroll,
.nested-scroll {
  position: relative;
  overflow-x: auto;
  max-width: 100%;
}

.expand-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: var(--control-height-sm);
  padding: 0;
  font-weight: 600;
  text-align: left;
  color: var(--text-primary);
}

.expand-btn:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}

.wrap-anywhere {
  overflow-wrap: anywhere;
}
</style>
