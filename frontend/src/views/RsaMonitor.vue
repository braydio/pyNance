<template>
  <BasePageLayout gap="gap-5">
    <PageHeader :icon="Activity">
      <template #title>RSA Monitor</template>
      <template #subtitle>
        {{ generatedLabel }}
      </template>
      <template #actions>
        <button class="refresh-button" type="button" :disabled="loading" @click="loadStatus">
          <RefreshCw class="refresh-icon" :class="{ spinning: loading }" aria-hidden="true" />
          <span>Refresh</span>
        </button>
      </template>
    </PageHeader>

    <div v-if="errorMessage" class="status-banner error">
      <AlertTriangle aria-hidden="true" />
      <span>{{ errorMessage }}</span>
    </div>

    <section v-if="monitorData" class="summary-grid">
      <article class="metric-panel">
        <span class="metric-label">Overall</span>
        <strong :class="['status-pill', statusClass(monitorData.overall_status)]">
          {{ monitorData.overall_status }}
        </strong>
      </article>
      <article class="metric-panel">
        <span class="metric-label">Heartbeat</span>
        <strong>{{ heartbeatLabel }}</strong>
        <small>{{ heartbeatAgeLabel }}</small>
      </article>
      <article class="metric-panel">
        <span class="metric-label">Queued Orders</span>
        <strong>{{ monitorData.orders.queue.count }}</strong>
        <small>{{ monitorData.orders.sent.count }} sent</small>
      </article>
      <article class="metric-panel">
        <span class="metric-label">AutoRSA Value</span>
        <strong>{{ formatCurrency(monitorData.account_history.total_value) }}</strong>
        <small>{{ monitorData.account_history.account_count || 0 }} accounts</small>
      </article>
    </section>

    <section v-if="monitorData" class="component-grid">
      <article
        v-for="component in monitorData.components"
        :key="component.name"
        class="component-panel"
      >
        <div class="panel-heading">
          <Server aria-hidden="true" />
          <div>
            <h2>{{ component.name }}</h2>
            <p>{{ component.root }}</p>
          </div>
        </div>
        <span :class="['status-pill', statusClass(component.status)]">{{ component.status }}</span>
      </article>
    </section>

    <section v-if="monitorData" class="content-grid">
      <article class="data-panel">
        <div class="panel-heading compact">
          <CheckCircle2 aria-hidden="true" />
          <h2>Sent Orders</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Time</th>
                <th>Ticker</th>
                <th>Action</th>
                <th>Qty</th>
                <th>Broker</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in recentOrders" :key="`${order.sent_at}-${order.ticker}`">
                <td>{{ formatDateTime(order.sent_at) }}</td>
                <td>{{ order.ticker || '-' }}</td>
                <td>{{ order.action || '-' }}</td>
                <td>{{ order.quantity ?? '-' }}</td>
                <td>{{ order.broker || '-' }}</td>
              </tr>
              <tr v-if="recentOrders.length === 0">
                <td colspan="5">No sent orders found.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="data-panel">
        <div class="panel-heading compact">
          <Clock aria-hidden="true" />
          <h2>AutoRSA Brokers</h2>
        </div>
        <div class="broker-list">
          <div v-for="broker in accountBrokers" :key="broker.name" class="broker-row">
            <span>{{ broker.name }}</span>
            <strong>{{ formatCurrency(broker.value) }}</strong>
            <small>{{ broker.accounts }} accounts</small>
          </div>
          <p v-if="accountBrokers.length === 0" class="empty-text">No account history found.</p>
        </div>
      </article>
    </section>

    <section v-if="monitorData" class="log-grid">
      <article v-for="log in monitorData.logs" :key="log.name" class="log-panel">
        <div class="panel-heading compact">
          <h2>{{ log.name }}</h2>
          <span :class="['status-pill', statusClass(log.status)]">{{ log.status }}</span>
        </div>
        <pre>{{ log.recent_lines.join('\n') || 'No recent lines found.' }}</pre>
      </article>
    </section>
  </BasePageLayout>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Activity, AlertTriangle, CheckCircle2, Clock, RefreshCw, Server } from 'lucide-vue-next'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import api from '@/services/api'

const monitorData = ref(null)
const loading = ref(false)
const errorMessage = ref('')
let refreshTimer = null

const generatedLabel = computed(() => {
  if (!monitorData.value?.generated_at) return 'Waiting for runtime data'
  return `Last checked ${formatDateTime(monitorData.value.generated_at)}`
})

const heartbeatLabel = computed(() => monitorData.value?.heartbeat?.status || 'unknown')
const heartbeatAgeLabel = computed(() => {
  const age = monitorData.value?.heartbeat?.age_seconds
  if (age === null || age === undefined) return 'No heartbeat age'
  if (age < 60) return `${age}s ago`
  return `${Math.round(age / 60)}m ago`
})

const recentOrders = computed(() => monitorData.value?.orders?.sent?.recent || [])
const accountBrokers = computed(() => monitorData.value?.account_history?.brokers || [])

async function loadStatus() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await api.fetchRsaMonitorStatus()
    monitorData.value = response.data
  } catch (error) {
    errorMessage.value = error?.response?.data?.message || 'Unable to load RSA monitor status.'
  } finally {
    loading.value = false
  }
}

function statusClass(status) {
  return {
    ok: 'ok',
    warning: 'warning',
    stale: 'warning',
    degraded: 'warning',
    missing: 'error',
    error: 'error',
    unknown: 'unknown',
  }[status || 'unknown']
}

function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

function formatCurrency(value) {
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

onMounted(() => {
  loadStatus()
  refreshTimer = window.setInterval(loadStatus, 30000)
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<style scoped>
.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 2.25rem;
  padding: 0.45rem 0.8rem;
  border: 1px solid var(--divider);
  border-radius: 8px;
  color: var(--color-text-light);
  background: var(--themed-bg, var(--color-bg-sec));
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.refresh-icon {
  width: 1rem;
  height: 1rem;
}

.spinning {
  animation: spin 1s linear infinite;
}

.status-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.9rem 1rem;
  border: 1px solid var(--divider);
  border-radius: 8px;
  background: var(--themed-bg, var(--color-bg-sec));
}

.status-banner.error {
  color: var(--color-error, #f87171);
}

.summary-grid,
.component-grid,
.content-grid,
.log-grid {
  display: grid;
  gap: 1rem;
}

.summary-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.component-grid,
.content-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.metric-panel,
.component-panel,
.data-panel,
.log-panel {
  border: 1px solid var(--divider);
  border-radius: 8px;
  background: var(--themed-bg, var(--color-bg-sec));
  box-shadow: 0 1px 2px var(--shadow);
}

.metric-panel {
  display: flex;
  min-height: 7rem;
  flex-direction: column;
  justify-content: space-between;
  padding: 1rem;
}

.metric-label,
.metric-panel small,
.broker-row small,
.panel-heading p,
.empty-text {
  color: var(--color-text-muted);
}

.metric-panel strong {
  color: var(--color-text-light);
  font-size: 1.35rem;
}

.component-panel,
.data-panel,
.log-panel {
  padding: 1rem;
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
}

.panel-heading > div {
  min-width: 0;
}

.panel-heading.compact {
  margin-bottom: 0.75rem;
  justify-content: flex-start;
}

.panel-heading svg {
  flex: 0 0 auto;
  width: 1.1rem;
  height: 1.1rem;
  color: var(--color-accent-yellow);
}

.panel-heading h2 {
  margin: 0;
  color: var(--color-text-light);
  font-size: 1rem;
  font-weight: 700;
}

.panel-heading p {
  max-width: 100%;
  margin: 0.15rem 0 0;
  overflow-wrap: anywhere;
  font-size: 0.82rem;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 1.7rem;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
}

.status-pill.ok {
  color: #86efac;
  background: rgb(22 101 52 / 0.24);
}

.status-pill.warning {
  color: #fde68a;
  background: rgb(180 83 9 / 0.24);
}

.status-pill.error {
  color: #fecaca;
  background: rgb(185 28 28 / 0.24);
}

.status-pill.unknown {
  color: var(--color-text-muted);
  background: var(--hover-bg);
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 0.55rem 0.4rem;
  border-bottom: 1px solid var(--divider);
  text-align: left;
  white-space: nowrap;
}

th {
  color: var(--color-text-muted);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

td {
  color: var(--color-text-light);
  font-size: 0.9rem;
}

.broker-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.broker-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 0.75rem;
  align-items: center;
}

.broker-row span {
  overflow: hidden;
  color: var(--color-text-light);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.broker-row strong {
  color: var(--color-text-light);
}

.log-grid {
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

pre {
  max-height: 22rem;
  margin: 0;
  overflow: auto;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  color: var(--color-text-light);
  font-size: 0.78rem;
  line-height: 1.45;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .broker-row {
    grid-template-columns: minmax(0, 1fr);
    gap: 0.15rem;
  }
}
</style>
