<!--
  TopAccountSnapshot.vue
  Displays accounts grouped with totals.
  Users can switch between groups, rename groups, and reorder accounts via drag handles.
-->
<template>
  <div class="bank-statement-list bs-collapsible w-full h-full">
    <div class="bs-toggle-row">
      <div class="bs-tabs-scroll" :style="{ '--accent': groupAccent }">
        <button
          v-if="groups.length > 3"
          class="bs-nav-btn"
          @click="shiftWindow(-1)"
          :disabled="visibleGroupIndex === 0"
          aria-label="Previous group"
        >
          &lt;
        </button>
        <TransitionGroup name="fade-in" tag="div" class="bs-tab-list">
          <template v-for="g in visibleGroups" :key="g.id">
            <input
              v-if="!g.name || editingGroupId === g.id"
              v-model="g.name"
              :class="[
                'bs-tab',
                activeGroupId === g.id && 'bs-tab-active',
                'bs-tab-' + g.id,
                'bs-tab-input',
              ]"
              @blur="finishEdit(g)"
              @keyup.enter="finishEdit(g)"
            />
            <button
              v-else
              :class="['bs-tab', activeGroupId === g.id && 'bs-tab-active', 'bs-tab-' + g.id]"
              @click="setActiveGroup(g.id)"
              @dblclick.stop="startEdit(g.id)"
              :aria-label="`Show ${g.name}`"
            >
              {{ g.name }}
            </button>
          </template>
          <button
            v-if="isEditingGroups"
            key="add-group"
            class="bs-tab bs-tab-add"
            @click="addGroup"
          >
            +
          </button>
        </TransitionGroup>
        <button
          v-if="groups.length > 3"
          class="bs-nav-btn"
          @click="shiftWindow(1)"
          :disabled="visibleGroupIndex + 3 >= groups.length"
          aria-label="Next group"
        >
          &gt;
        </button>
      </div>
      <div class="bs-group-dropdown" :style="{ '--accent': groupAccent }">
        <button class="bs-group-btn" @click="toggleGroupMenu" aria-label="Select account group">
          {{ activeGroup ? activeGroup.name : 'Select group' }} ▾
        </button>
        <Transition name="slide-down">
          <ul v-if="showGroupMenu" class="bs-group-menu">
            <li v-for="g in groups" :key="g.id">
              <button class="bs-group-item" @click="selectGroup(g.id)">
                {{ g.name || '(unnamed)' }}
              </button>
            </li>
            <li>
              <button class="bs-group-item" @click="toggleEditGroups">
                {{ isEditingGroups ? 'Done' : 'Edit' }}
              </button>
            </li>
          </ul>
        </Transition>
      </div>
    </div>

    <Transition name="bs-slide">
      <draggable
        v-if="activeGroup"
        v-model="activeGroup.accounts"
        handle=".bs-drag-handle"
        item-key="id"
        tag="ul"
        class="bs-list"
      >
        <template #item="{ element: account }">
          <li class="bs-account-container">
            <div
              class="bs-row"
              :style="{ '--accent': accentColor(account) }"
              @click="toggleDetails(account.id)"
              role="button"
              tabindex="0"
              @keydown.enter="toggleDetails(account.id)"
              @keydown.space="toggleDetails(account.id)"
            >
              <GripVertical class="bs-drag-handle" @mousedown.stop @touchstart.stop />

              <div class="bs-stripe"></div>
              <div class="bs-logo-container">
                <img
                  v-if="account.institution_icon_url"
                  :src="account.institution_icon_url"
                  alt="Bank logo"
                  class="bs-logo"
                  loading="lazy"
                />
                <span v-else class="bs-logo-fallback">{{ initials(account.name) }}</span>
              </div>
              <div class="bs-details">
                <div class="bs-name">
                  <span
                    class="bs-toggle-icon"
                    :class="{ 'bs-expanded': openAccountId === account.id }"
                    >▶</span
                  >
                  {{ account.name }}
                </div>
                <div class="bs-mask">
                  <span v-if="account.mask">•••• {{ mask(account.mask) }}</span>
                  <span
                    v-else
                    class="bs-no-mask-icon"
                    role="img"
                    aria-label="Account number unavailable"
                    >∗</span
                  >
                </div>
              </div>
              <div class="bs-sparkline">
                <AccountSparkline :account-id="account.id" />
              </div>
              <div class="bs-amount-section">
                <span class="bs-amount">{{ format(account.adjusted_balance) }}</span>
              </div>
            </div>
            <div v-if="openAccountId === account.id" class="bs-details-row">
              <div class="bs-details-content">
                <ul class="bs-details-list">
                  <li
                    v-for="tx in recentTxs[account.id]"
                    :key="tx.transaction_id || tx.id"
                    class="bs-tx-row"
                  >
                    <span class="bs-tx-date">{{ tx.date || tx.transaction_date || '' }}</span>
                    <span class="bs-tx-name">{{
                      tx.merchant_name || tx.name || tx.description
                    }}</span>
                    <span class="bs-tx-amount">{{ format(tx.amount) }}</span>
                  </li>
                  <li v-if="recentTxs[account.id]?.length === 0" class="bs-tx-empty">
                    No recent transactions
                  </li>
                </ul>
              </div>
            </div>
          </li>
        </template>
        <template #footer>
          <li
            v-if="activeAccounts.length"
            class="bs-summary-row"
            :style="{ '--accent': groupAccent }"
          >
            <div></div>
            <div class="bs-summary-label">Total {{ activeGroup.name }}</div>
            <div class="bs-summary-amount">
              {{ format(activeTotal) }}
            </div>
          </li>
        </template>
      </draggable>
    </Transition>

    <div v-if="activeGroup && !activeGroup.accounts.length" class="bs-empty">
      No accounts to display
    </div>

    <!-- liabilities section removed -->
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import draggable from 'vuedraggable'
import { GripVertical } from 'lucide-vue-next'
import { useTopAccounts } from '@/composables/useTopAccounts'
import { useAccountGroups } from '@/composables/useAccountGroups'
import AccountSparkline from './AccountSparkline.vue'
import { fetchRecentTransactions } from '@/api/accounts'
const props = defineProps({
  accountSubtype: { type: String, default: '' },
  useSpectrum: { type: Boolean, default: false },
})

// full account list used for group editing
const { allVisibleAccounts, fetchAccounts } = useTopAccounts(toRef(props, 'accountSubtype'))
const { groups, activeGroupId } = useAccountGroups()
onMounted(fetchAccounts)

// initialize groups from loaded accounts
watch(allVisibleAccounts, (acctList) => {
  const assets = acctList ? acctList.filter((a) => a.adjusted_balance >= 0) : []
  const liabilities = acctList ? acctList.filter((a) => a.adjusted_balance < 0) : []
  const assetGroup = groups.value.find((g) => g.id === 'assets')
  const liabilityGroup = groups.value.find((g) => g.id === 'liabilities')

  if (!assetGroup && !liabilityGroup && groups.value.every((g) => !g.accounts.length)) {
    // first-time setup: replace default group with auto groups
    groups.value = [
      {
        id: 'assets',
        name: 'Assets',
        color: 'var(--color-accent-cyan)',
        accounts: assets,
      },
      {
        id: 'liabilities',
        name: 'Liabilities',
        color: 'var(--color-accent-yellow)',
        accounts: liabilities,
      },
    ]
    activeGroupId.value = assets.length ? 'assets' : 'liabilities'
    return
  }

  if (assetGroup) {
    assetGroup.accounts = assets
    assetGroup.color = assetGroup.color || 'var(--color-accent-cyan)'
  } else {
    groups.value.push({
      id: 'assets',
      name: 'Assets',
      color: 'var(--color-accent-cyan)',
      accounts: assets,
    })
  }

  if (liabilityGroup) {
    liabilityGroup.accounts = liabilities
    liabilityGroup.color = liabilityGroup.color || 'var(--color-accent-yellow)'
  } else {
    groups.value.push({
      id: 'liabilities',
      name: 'Liabilities',
      color: 'var(--color-accent-yellow)',
      accounts: liabilities,
    })
  }
})

// Details dropdown state
const openAccountId = ref(null)
const recentTxs = reactive({})

/** Toggle details dropdown for an account and load recent transactions */
function toggleDetails(accountId) {
  openAccountId.value = openAccountId.value === accountId ? null : accountId
  if (openAccountId.value === accountId && !recentTxs[accountId]) {
    fetchRecentTransactions(accountId, 3)
      .then((res) => {
        let txs = []
        if (Array.isArray(res?.transactions)) {
          txs = res.transactions
        } else if (Array.isArray(res?.data?.transactions)) {
          txs = res.data.transactions
        } else if (Array.isArray(res?.data)) {
          txs = res.data
        }
        recentTxs[accountId] = txs
      })
      .catch(() => {
        recentTxs[accountId] = []
      })
  }
}

const showGroupMenu = ref(false)
const editingGroupId = ref(null)
const isEditingGroups = ref(false)

const activeGroup = computed(() => groups.value.find((g) => g.id === activeGroupId.value) || null)
const groupAccent = computed(() => activeGroup.value?.color || 'var(--color-accent-cyan)')

const visibleGroupIndex = ref(0)
const visibleGroups = computed(() =>
  groups.value.slice(visibleGroupIndex.value, visibleGroupIndex.value + 3),
)

/** Shift the visible tab window left or right */
function shiftWindow(direction) {
  const maxStart = Math.max(0, groups.value.length - 3)
  visibleGroupIndex.value = Math.min(maxStart, Math.max(0, visibleGroupIndex.value + direction))
}

/** Keep active group within the visible range */
watch(activeGroupId, (id) => {
  const idx = groups.value.findIndex((g) => g.id === id)
  if (idx === -1) return
  if (idx < visibleGroupIndex.value) {
    visibleGroupIndex.value = idx
  } else if (idx > visibleGroupIndex.value + 2) {
    visibleGroupIndex.value = idx - 2
  }
})

/** Adjust window when group list changes */
watch(
  () => groups.value.length,
  (len) => {
    const maxStart = Math.max(0, len - 3)
    if (visibleGroupIndex.value > maxStart) {
      visibleGroupIndex.value = maxStart
    }
  },
)

const spectrum = [
  'var(--color-accent-cyan)',
  'var(--color-accent-yellow)',
  'var(--color-accent-red)',
  'var(--color-accent-blue)',
]

/** Return accent color for an account */
function accentColor(account, index) {
  if (props.useSpectrum) {
    const subtype = (account.subtype || '').toLowerCase()
    const map = {
      checking: 'var(--color-accent-cyan)',
      savings: 'var(--color-accent-blue)',
      credit: 'var(--color-accent-red)',
      'credit card': 'var(--color-accent-red)',
      loan: 'var(--color-accent-yellow)',
    }
    return map[subtype] || spectrum[index % spectrum.length]
  }
  return account.adjusted_balance >= 0 ? 'var(--color-accent-cyan)' : 'var(--color-accent-yellow)'
}

function setActiveGroup(id) {
  activeGroupId.value = id
}

function toggleGroupMenu() {
  showGroupMenu.value = !showGroupMenu.value
}

function selectGroup(id) {
  setActiveGroup(id)
  showGroupMenu.value = false
}

function toggleEditGroups() {
  isEditingGroups.value = !isEditingGroups.value
  showGroupMenu.value = false
}

/** Enable editing for a group tab */
function startEdit(id) {
  editingGroupId.value = id
}

/** Disable editing and persist the group name */
function finishEdit(group) {
  editingGroupId.value = null
  if (!group.name) {
    editingGroupId.value = group.id
  }
}

/** Create a new group and start editing its name */
function addGroup() {
  const id = `group-${Date.now()}`
  groups.value.push({
    id,
    name: '',
    accounts: [],
    accent: 'var(--color-accent-cyan)',
  })
  selectGroup(id)
  editingGroupId.value = id
}

const activeAccounts = computed(() => (activeGroup.value ? activeGroup.value.accounts : []))
const activeTotal = computed(() =>
  activeGroup.value
    ? activeGroup.value.accounts.reduce((sum, a) => sum + a.adjusted_balance, 0)
    : 0,
)

const format = (val) => {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  if (typeof val !== 'number') return ''
  if (val < 0) {
    return `(${formatter.format(Math.abs(val))})`
  }
  return formatter.format(val)
}

function mask(maskString) {
  if (!maskString) return null
  return maskString.toString().slice(-4)
}
function initials(name) {
  if (!name) return '??'
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
</script>

<style scoped>
/* Account details dropdown styles */
.bs-details-btn-section {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.bs-details-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  transition: background 0.2s;
}
.bs-details-btn:hover {
  background: var(--color-bg-dark);
}
.bs-details-row {
  grid-column: 1 / -1;
  background: var(--color-bg-dark);
  padding: 0.5rem 1rem;
}
.bs-details-content {
  font-size: 0.85rem;
  color: var(--color-text-light);
}
.bs-details-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.bs-tx-row {
  display: flex;
  justify-content: space-between;
  padding: 0.25rem 0;
  border-bottom: 1px solid var(--divider);
}
.bs-tx-date {
  flex: 0 0 auto;
  width: 5ch;
  color: var(--color-text-muted);
}
.bs-tx-name {
  flex: 1 1 auto;
  padding: 0 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bs-tx-amount {
  flex: 0 0 auto;
  width: 7ch;
  text-align: right;
}
.bs-tx-empty {
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
  padding: 0.5rem 0;
}
.bank-statement-list {
  max-width: unset;
  margin: 0;
  padding: 0;
  border-radius: 1.3rem;
  user-select: none;
  width: 100%;
  height: 100%;
  background: transparent;
  box-shadow: none;
  border: none;
}

.bs-toggle-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.7rem;
  margin-bottom: 1.1rem;
  background: transparent;
  border-radius: 1rem 1rem 0 0;
}

.bs-tabs-scroll {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  overflow: hidden;
}

.bs-tab-list {
  display: flex;
  align-items: center;
  gap: 0.7rem;
}

.bs-tabs-scroll::-webkit-scrollbar {
  display: none;
}

.bs-tab {
  padding: 0.5rem 1rem;
  background: var(--color-bg-sec);
  color: var(--color-accent-cyan);
  border: 1px solid var(--divider);
  border-radius: 0.8rem 0.8rem 0 0;
  font-size: 1rem;
  font-weight: 600;
  transition:
    background 0.2s,
    color 0.2s;
  cursor: pointer;
  position: relative;
}

.bs-tab-input {
  cursor: text;
}

.bs-tab-input:focus {
  outline: none;
}

.bs-tab-active.bs-tab-assets {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-cyan) 100%);
  color: var(--color-accent-cyan);
  z-index: 2;
}

.bs-tab-active.bs-tab-liabilities {
  background: linear-gradient(90deg, var(--color-bg-dark) 70%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
  z-index: 2;
}

/* Hover state retains original gradient styling */

.bs-tab-liabilities:hover,
.bs-tab-liabilities:focus-visible {
  background: linear-gradient(90deg, var(--color-bg-dark) 85%, var(--color-accent-yellow) 100%);
  color: var(--color-accent-yellow);
}

.bs-group-dropdown {
  position: relative;
  margin-left: auto;
  flex-shrink: 0;
}

.bs-group-btn {
  padding: 0.4rem 0.8rem;
  background: var(--color-bg-sec);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 0.8rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  transition:
    background 0.2s,
    color 0.2s;
}

.bs-nav-btn {
  padding: 0.4rem 0.6rem;
  background: var(--color-bg-sec);
  color: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 0.8rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    background 0.2s,
    color 0.2s;
}

.bs-nav-btn:hover,
.bs-nav-btn:focus-visible {
  background: var(--accent);
  color: var(--color-bg-dark);
}

.bs-nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bs-group-btn:hover,
.bs-group-btn:focus-visible {
  background: var(--accent);
  color: var(--color-bg-dark);
}

.bs-group-menu {
  position: absolute;
  right: 0;
  margin-top: 0.2rem;
  background: var(--color-bg-sec);
  border: 1px solid var(--accent);
  border-radius: 0.5rem;
  z-index: 10;
  display: flex;
  flex-direction: column;
  min-width: 8rem;
  padding: 0.2rem 0;
}

.bs-group-item {
  padding: 0.4rem 0.8rem;
  background: transparent;
  color: var(--color-text-light);
  border: none;
  text-align: left;
  cursor: pointer;
}

.bs-group-item:hover,
.bs-group-item:focus-visible {
  background: var(--accent);
  color: var(--color-bg-dark);
}

.bs-tab-add {
  font-weight: 700;
  text-align: center;
}

.bs-group-editor {
  display: flex;
  flex-direction: column;
}

.bs-account-dropdown {
  margin-top: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.bs-account-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.bs-list {
  display: flex;
  flex-direction: column;
  gap: 1.46rem;
  /* Increased gap for more separation */
  margin: 0;
  padding: 0.22rem 0.22rem 0.22rem 0.16rem;
  list-style: none;
}

.bs-row {
  display: grid;
  grid-template-columns: auto auto 1fr auto auto;
  align-items: center;
  background: linear-gradient(90deg, var(--color-bg-dark) 80%, var(--color-bg-sec) 100%);
  border-radius: 11px;
  padding: 0.39rem 0.45rem 0.39rem 0.1rem;
  box-shadow: 0 2px 14px var(--shadow, #1c274055);
  position: relative;
  border: 2px solid var(--accent, var(--color-accent-cyan));
  border-left: 6px solid var(--accent, var(--color-accent-cyan));
  min-height: 36px;
  gap: 0.45rem;
  will-change: transform, box-shadow;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.bs-row:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px var(--shadow, #1c274077);
  border-color: var(--accent, var(--color-accent-cyan));
}

.bs-row:focus {
  outline: 2px solid var(--accent, var(--color-accent-cyan));
  outline-offset: 2px;
}

.bs-row:active {
  transform: translateY(0);
}

.bs-sparkline {
  width: 60px;
  height: 20px;
  align-self: center;
  color: var(--accent, var(--color-accent-cyan));
}

.bs-no-mask-icon {
  display: inline-block;
  color: var(--accent, var(--color-accent-cyan));
  font-size: 0.8rem;
}

.bs-drag-handle {
  cursor: grab;
  color: var(--accent, var(--color-accent-cyan));
  display: flex;
  align-items: center;
}

.bs-drag-handle:active {
  cursor: grabbing;
}

.bs-stripe {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 6px;
  border-radius: 8px 0 0 8px;
  z-index: 1;
  opacity: 0.75;
  pointer-events: none;
  background: var(--accent, var(--color-accent-cyan));
}

.bs-logo-container {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-bg-dark);
  box-shadow: 0 2px 10px var(--shadow, #364b7a16);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  border: 1.7px solid var(--accent, var(--color-accent-cyan));
  overflow: hidden;
}

.bs-logo {
  width: 20px;
  height: 20px;
  object-fit: contain;
  display: block;
  border-radius: 50%;
  background: #fff;
}

.bs-logo-fallback {
  font-size: 0.89rem;
  font-weight: 700;
  color: var(--accent, var(--color-accent-cyan));
  text-align: center;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg-sec);
}

.bs-details {
  min-width: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 2;
  overflow: hidden;
}

.bs-name {
  font-size: 0.97rem;
  font-weight: 600;
  color: var(--accent, var(--color-accent-cyan));
  letter-spacing: 0.01em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.bs-toggle-icon {
  font-size: 0.7rem;
  color: var(--accent, var(--color-accent-cyan));
  transition: transform 0.3s ease;
  display: inline-block;
  opacity: 0.8;
  flex-shrink: 0;
}

.bs-toggle-icon.bs-expanded {
  transform: rotate(90deg);
  opacity: 1;
}

.bs-row:hover .bs-toggle-icon {
  opacity: 1;
  color: var(--accent, var(--color-accent-cyan));
}

.bs-mask {
  font-size: 0.81rem;
  color: var(--accent, var(--color-accent-cyan));
  opacity: 0.87;
  margin-top: 1px;
  letter-spacing: 0.03em;
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
  max-width: 100%;
}

.bs-amount-section {
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  height: 100%;
  z-index: 2;
}

.bs-amount {
  font-size: 1.01rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  min-width: 4.6ch;
  text-align: right;
  padding-right: 0.13em;
  margin-left: 0.2em;
  word-break: keep-all;
  color: var(--accent, var(--color-accent-cyan));
}

.bs-empty {
  color: var(--color-text-muted);
  font-style: italic;
  padding: 1.2rem 0 0.7rem 0;
  text-align: center;
  font-size: 1.01rem;
}

.bs-summary-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  border-top: 1.5px solid var(--accent, var(--color-accent-cyan));
  margin-top: 0.12rem;
  padding: 0.18rem 0.12rem 0.12rem 0.06rem;
  background: transparent;
  min-height: 24px;
}

.bs-summary-label {
  font-size: 0.91rem;
  color: var(--color-text-muted);
  font-weight: 600;
  text-align: right;
}

.bs-summary-amount {
  font-size: 1.02rem;
  font-weight: 700;
  text-align: right;
  color: var(--accent, var(--color-accent-cyan));
}

/* New account container and themed button styles */
.bs-account-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bs-details-btn-row {
  display: flex;
  justify-content: center;
  padding: 0.2rem 0.8rem;
}

.bs-details-btn-themed {
  background: linear-gradient(135deg, var(--color-bg-sec) 0%, var(--color-bg-dark) 100%);
  border: 1px solid var(--color-accent-cyan);
  color: var(--color-accent-cyan);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  padding: 0.4rem 0.8rem;
  border-radius: 0.6rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  letter-spacing: 0.02em;
}

.bs-details-btn-themed:hover {
  background: linear-gradient(135deg, var(--color-accent-cyan) 0%, var(--color-accent-blue) 100%);
  color: var(--color-bg-dark);
  border-color: var(--color-accent-cyan);
  box-shadow: 0 4px 16px rgba(99, 205, 207, 0.3);
  transform: translateY(-1px);
}

.bs-details-btn-themed:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.bs-btn-icon {
  font-size: 0.7rem;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.bs-details-btn-themed:hover .bs-btn-icon {
  opacity: 1;
}

/* Animations */
.bs-slide-enter-active,
.bs-slide-leave-active {
  transition: all 0.45s cubic-bezier(0.44, 0.11, 0.42, 1.07);
}

.bs-slide-enter-from {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}

.bs-slide-leave-to {
  opacity: 0;
  transform: translateY(-15px) scale(0.97);
}

.fade-in-enter-active {
  animation: fade-in 0.3s ease;
}

@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Responsive */
@media (max-width: 630px) {
  .bank-statement-list {
    padding: 0.18rem 0.08rem 0.45rem 0.08rem;
    max-width: 99vw;
  }

  .bs-tab {
    padding: 0.54rem 0.9rem 0.54rem 0.8rem;
    font-size: 0.89rem;
  }

  .bs-group-btn {
    padding: 0.45rem 0.75rem;
    font-size: 0.8rem;
  }

  .bs-nav-btn {
    padding: 0.45rem 0.6rem;
    font-size: 0.8rem;
  }

  .bs-tabs-scroll {
    overflow: hidden;
  }

  .bs-tab-list {
    flex-wrap: nowrap;
  }

  .bs-group-dropdown {
    margin-left: 0.4rem;
  }

  .bs-list {
    padding: 0.1rem 0.05rem 0.1rem 0.05rem;
  }

  .bs-row {
    padding: 0.32rem 0.22rem 0.32rem 0.05rem;
    min-height: 27px;
  }

  .bs-summary-row {
    padding: 0.12rem 0.08rem 0.09rem 0.04rem;
  }
}
</style>
