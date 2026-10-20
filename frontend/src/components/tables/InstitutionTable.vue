<template>
  <div class="institution-table">
    <p v-if="loading" class="text-sm text-muted" role="status">Loading institutions…</p>
    <div v-else-if="loadError" role="alert" class="text-sm">
      <p class="text-negative">Unable to load institutions.</p>
      <button type="button" class="btn btn-sm" @click="fetch">Retry</button>
    </div>
    <p v-else-if="!institutions.length" class="text-sm text-muted">No institutions linked yet.</p>
    <div v-else class="ledger">
      <div class="ledger-scroll institution-scroll">
        <table class="ledger-table">
          <caption class="ledger-caption--sr">
            Linked institutions ({{
              institutions.length
            }})
          </caption>
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col">Provider</th>
              <th scope="col">Last Refresh</th>
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
                  <div class="ledger-secondary" :data-testid="`institution-summary-${inst.id}`">
                    {{ summaryLine(inst) }}
                  </div>
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
                  <div :id="`institution-panel-${inst.id}`">
                    <table class="ledger-table">
                      <caption class="ledger-caption--sr">
                        Accounts at
                        {{
                          inst.name
                        }}
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Account</th>
                          <th scope="col">Type</th>
                          <th scope="col" class="ledger-num">Balance</th>
                          <th scope="col">Link</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="acc in inst.accounts" :key="acc.account_id">
                          <td class="wrap-anywhere">{{ acc.name }}</td>
                          <td>{{ acc.subtype || acc.type }}</td>
                          <td class="ledger-num">
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
  </div>
</template>

<script>
import api from '@/services/api'
import { portfolioTotals } from '@/utils/accountPortfolio'
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
    /** Type-aware one-line summary: counts, assets and liabilities never netted blindly. */
    summaryLine(inst) {
      const accounts = inst.accounts || []
      const totals = portfolioTotals(accounts)
      const money = (v) => (v === null ? 'Unavailable' : this.formatBalance(v))
      const parts = [`${totals.accountCount} account${totals.accountCount === 1 ? '' : 's'}`]
      parts.push(`assets ${money(totals.assets)}`)
      if (totals.liabilities) parts.push(`owed ${money(totals.liabilities)}`)
      if (totals.unknownBalances) parts.push(`${totals.unknownBalances} balance unavailable`)
      if (totals.hiddenCount) parts.push(`${totals.hiddenCount} hidden not counted`)
      return parts.join(' · ')
    },
    formatBalance(b) {
      if (b === null || b === undefined || b === '') return 'Unavailable'
      const num = parseFloat(b)
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
/* position: relative keeps absolutely positioned helpers (e.g. .sr-only) inside the region
   instead of letting them extend the document's scrollable width. */
.institution-scroll {
  position: relative;
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
