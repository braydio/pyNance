<!--
  TopAccountSnapshot.vue
  Displays accounts grouped with totals.
  Users can switch between groups, rename groups, reorder them via drag handles,
  remove groups, and add or remove accounts when editing mode is enabled.
-->

<!-- TopAccountSnapshot.vue -->
<template>
  <div
    class="bank-statement-list bs-collapsible w-full h-full"
    :class="{ 'bs-editing': isEditingGroups }"
    :style="{ '--accent': groupAccent }"
  >
    <div class="bs-header-row">
      <div class="bs-group-banner">
        <div class="bs-group-title">
          <div
            v-if="isEditingGroups"
            class="bs-title-field"
            :class="{ 'is-active': isRenamingTitle }"
            @click="startTitleEdit"
            @dblclick.stop
          >
            <input
              v-if="isRenamingTitle"
              v-model="activeGroupNameDraft"
              class="bs-title-input"
              maxlength="30"
              @blur="finishActiveTitleEdit"
              @keyup.enter="finishActiveTitleEdit"
            />
            <span v-else class="bs-group-name muted" :title="effectiveGroup?.name || 'Group'">
              {{ effectiveGroup?.name || 'Group' }}
            </span>
            <button
              v-if="isRenamingTitle"
              type="button"
              class="bs-rename-btn"
              @click.stop="finishActiveTitleEdit"
            >
              Rename
            </button>
          </div>
          <template v-else>
            <span class="bs-group-name" :title="effectiveGroup?.name || 'Group'">
              {{ effectiveGroup?.name || 'Group' }}
            </span>
          </template>
        </div>
        <div class="bs-banner-meta">
          <span class="bs-banner-label">Total Balance</span>
          <span class="bs-banner-value" :class="totalValueClass">
            {{ format(visibleTotal) }}
          </span>
        </div>
      </div>
    </div>
    <!-- Group Selector -->
    <div class="bs-toggle-row">
      <div class="bs-group-dropdown" :style="{ '--accent': groupAccent }">
        <button
          ref="groupMenuButtonRef"
          type="button"
          :class="groupDropdownClasses"
          @click="toggleGroupMenu"
          aria-label="Switch group"
        >
          Switch ▾
        </button>
        <Transition name="slide-down">
          <Draggable
            v-if="showGroupMenu && isEditingGroups"
            ref="groupMenuRef"
            v-model="groups"
            item-key="id"
            handle=".bs-group-handle"
            tag="ul"
            class="bs-group-menu"
            @end="persistGroupOrder"
          >
            <template #item="{ element: g }">
              <li :key="g.id" class="bs-group-row">
                <GripVertical class="bs-group-handle" aria-hidden="true" />
                <template v-if="editingGroupId === g.id">
                  <input
                    v-model="g.name"
                    class="bs-group-input"
                    maxlength="30"
                    @blur="finishEdit(g)"
                    @keyup.enter="finishEdit(g)"
                  />
                </template>
                <template v-else>
                  <button
                    type="button"
                    class="bs-group-item"
                    :class="{
                      'bs-group-item-active': g.id === activeGroupId,
                      'is-active': g.id === activeGroupId,
                    }"
                    :aria-pressed="g.id === activeGroupId"
                    @click="selectGroup(g.id)"
                    @dblclick.stop="startEdit(g.id)"
                  >
                    <Check v-if="g.id === activeGroupId" class="bs-group-check" />
                    {{ g.name || '(unnamed)' }}
                  </button>
                </template>
                <button
                  type="button"
                  class="bs-group-delete"
                  aria-label="Remove group"
                  @click.stop="removeGroup(g.id)"
                >
                  <X />
                </button>
              </li>
            </template>
            <template #footer>
              <li>
                <button
                  type="button"
                  class="bs-group-item bs-group-action gradient-toggle-btn"
                  @click="addGroup"
                  aria-label="Add account group"
                >
                  + Add group
                </button>
              </li>
              <li>
                <button
                  type="button"
                  class="bs-group-item bs-group-action gradient-toggle-btn"
                  @click="finishEditingSession"
                  aria-label="Finish editing account groups"
                >
                  Done
                </button>
              </li>
            </template>
          </Draggable>
          <ul v-else-if="showGroupMenu" ref="groupMenuRef" class="bs-group-menu">
            <li v-for="g in groups" :key="g.id" class="bs-group-row">
              <button
                type="button"
                class="bs-group-item"
                :class="{
                  'bs-group-item-active': g.id === activeGroupId,
                  'is-active': g.id === activeGroupId,
                }"
                :aria-pressed="g.id === activeGroupId"
                @click="selectGroup(g.id)"
              >
                <Check v-if="g.id === activeGroupId" class="bs-group-check" />
                {{ g.name || '(unnamed)' }}
              </button>
            </li>
            <li>
              <button
                type="button"
                class="bs-group-item bs-group-action gradient-toggle-btn"
                @click="toggleEditGroups(true)"
                aria-label="Edit account groups"
              >
                Edit groups
              </button>
            </li>
          </ul>
        </Transition>
      </div>
    </div>

    <!-- Render draggable without container Transition to avoid DOM detachment issues -->
    <Draggable
      :key="activeGroupId"
      v-if="effectiveGroup"
      v-model="groupAccounts"
      item-key="id"
      handle=".bs-drag-handle"
      tag="ul"
      class="bs-list"
      @end="persistAccountOrder"
    >
      <template #item="{ element: account }">
        <li class="bs-account-container" :key="accountId(account)">
          <!-- Enter and space should toggle details without moving focus -->
          <div
            class="bs-row"
            :style="{ '--accent': accentColor(account) }"
            @click="toggleDetails(accountId(account), $event)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="toggleDetails(accountId(account), $event)"
            @keydown.space.prevent="toggleDetails(accountId(account), $event)"
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
                  :class="{ 'bs-expanded': openAccountId === accountId(account) }"
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
              <div v-if="creditUtilization(account)" class="bs-utilization">
                <div class="bs-utilization-header">
                  <span class="bs-utilization-label">Utilization</span>
                  <span class="bs-utilization-percent">
                    {{ creditUtilization(account).percentLabel }}
                  </span>
                </div>
                <div
                  class="bs-utilization-bar"
                  role="progressbar"
                  :aria-valuenow="creditUtilization(account).percent"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div
                    class="bs-utilization-fill"
                    :style="{ width: `${creditUtilization(account).barPercent}%` }"
                  ></div>
                </div>
                <div class="bs-utilization-text">
                  {{ creditUtilization(account).balanceLabel }} of
                  {{ creditUtilization(account).limitLabel }}
                </div>
              </div>
            </div>
            <div class="bs-sparkline">
              <AccountSparkline :account-id="accountId(account)" />
            </div>
            <div class="bs-amount-section">
              <div class="bs-amount-stack">
                <span class="bs-amount" :class="balanceClass(account)">{{
                  format(resolveAccountBalance(account))
                }}</span>
                <div v-if="showUtilization(account)" class="bs-utilization">
                  <span class="bs-utilization-label">Utilization</span>
                  <span class="bs-utilization-value">{{ formatUtilization(account) }}</span>
                  <span class="bs-utilization-bar" aria-hidden="true">
                    <span
                      class="bs-utilization-fill"
                      :style="{ width: utilizationWidth(account) }"
                    ></span>
                  </span>
                </div>
              </div>
              <X
                v-if="isEditingGroups"
                class="bs-account-delete"
                @click.stop="removeAccount(accountId(account))"
              />
            </div>
          </div>
          <div v-if="openAccountId === accountId(account)" class="bs-details-row">
            <div class="bs-details-content">
              <ul class="bs-details-list">
                <li
                  v-for="tx in recentTxs[accountId(account)]"
                  :key="tx.transaction_id || tx.id"
                  class="bs-tx-row"
                >
                  <span class="bs-tx-date">{{
                    formatShortDate(tx.date || tx.transaction_date || '')
                  }}</span>
                  <span class="bs-tx-name">{{
                    tx.merchant_name || tx.name || tx.description
                  }}</span>
                  <span class="bs-tx-amount" :class="amountClass(tx.amount)">{{
                    format(tx.amount)
                  }}</span>
                </li>
                <li v-if="recentTxs[accountId(account)]?.length === 0" class="bs-tx-empty">
                  No recent transactions
                </li>
              </ul>
            </div>
          </div>
        </li>
      </template>
      <!-- Add Account + Summary -->
      <template #footer>
        <li
          v-if="isEditingGroups || activeAccounts.length === 0"
          class="bs-account-container bs-add-account"
          :class="{ 'bs-disabled': activeAccounts.length >= MAX_ACCOUNTS_PER_GROUP }"
          :key="'add-' + activeGroupId"
        >
          <div v-if="showAccountSelector" class="bs-row">
            <select v-model="selectedAccountId" @change="confirmAddAccount" class="bs-add-select">
              <option value="" disabled>Select account</option>
              <option
                v-for="acct in availableAccounts"
                :key="accountId(acct)"
                :value="accountId(acct)"
              >
                {{ acct.name }}
              </option>
            </select>
          </div>
          <div
            v-else
            class="bs-row bs-add-placeholder"
            @click="startAddAccount"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="startAddAccount"
            @keydown.space.prevent="startAddAccount"
          >
            <div class="bs-details">
              <div class="bs-name">Add Account</div>
            </div>
          </div>
        </li>
      </template>
    </Draggable>

    <div v-else-if="fallbackAccounts.length" class="bs-fallback">
      <p class="bs-fallback-note">
        {{
          offlineMode
            ? 'Showing your top accounts while local changes sync back online.'
            : 'No accounts configured yet — displaying your highest balances by default.'
        }}
      </p>
      <ul class="bs-list bs-list--static">
        <li
          v-for="account in fallbackAccounts"
          :key="accountId(account)"
          class="bs-account-container"
        >
          <div
            class="bs-row bs-row--static"
            :style="{ '--accent': accentColor(account) }"
            @click="toggleDetails(accountId(account), $event)"
            role="button"
            tabindex="0"
            @keydown.enter.prevent="toggleDetails(accountId(account), $event)"
            @keydown.space.prevent="toggleDetails(accountId(account), $event)"
          >
            <div class="bs-static-spacer" aria-hidden="true"></div>
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
              <div class="bs-name">{{ account.name }}</div>
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
              <div v-if="creditUtilization(account)" class="bs-utilization">
                <div class="bs-utilization-header">
                  <span class="bs-utilization-label">Utilization</span>
                  <span class="bs-utilization-percent">
                    {{ creditUtilization(account).percentLabel }}
                  </span>
                </div>
                <div
                  class="bs-utilization-bar"
                  role="progressbar"
                  :aria-valuenow="creditUtilization(account).percent"
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div
                    class="bs-utilization-fill"
                    :style="{ width: `${creditUtilization(account).barPercent}%` }"
                  ></div>
                </div>
                <div class="bs-utilization-text">
                  {{ creditUtilization(account).balanceLabel }} of
                  {{ creditUtilization(account).limitLabel }}
                </div>
              </div>
            </div>
            <div class="bs-sparkline">
              <AccountSparkline :account-id="accountId(account)" />
            </div>
            <div class="bs-amount-section">
              <div class="bs-amount-stack">
                <span class="bs-amount" :class="balanceClass(account)">{{
                  format(resolveAccountBalance(account))
                }}</span>
                <div v-if="showUtilization(account)" class="bs-utilization">
                  <span class="bs-utilization-label">Utilization</span>
                  <span class="bs-utilization-value">{{ formatUtilization(account) }}</span>
                  <span class="bs-utilization-bar" aria-hidden="true">
                    <span
                      class="bs-utilization-fill"
                      :style="{ width: utilizationWidth(account) }"
                    ></span>
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="openAccountId === accountId(account)" class="bs-details-row">
            <div class="bs-details-content">
              <ul class="bs-details-list">
                <li
                  v-for="tx in recentTxs[accountId(account)]"
                  :key="tx.transaction_id || tx.id"
                  class="bs-tx-row"
                >
                  <span class="bs-tx-date">{{
                    formatShortDate(tx.date || tx.transaction_date || '')
                  }}</span>
                  <span class="bs-tx-name">{{
                    tx.merchant_name || tx.name || tx.description
                  }}</span>
                  <span class="bs-tx-amount" :class="amountClass(tx.amount)">{{
                    format(tx.amount)
                  }}</span>
                </li>
                <li v-if="recentTxs[accountId(account)]?.length === 0" class="bs-tx-empty">
                  No recent transactions
                </li>
              </ul>
            </div>
          </div>
        </li>
      </ul>
    </div>
    <div v-else class="bs-empty">No accounts to display</div>

    <div v-if="isEditingGroups" class="bs-editing-footer">
      <span class="bs-editing-chip">Editing groups</span>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import Draggable from 'vuedraggable'
import { GripVertical, X, Check } from 'lucide-vue-next'
import { useTopAccounts } from '@/composables/useTopAccounts'
import { useAccountGroups } from '@/composables/useAccountGroups'
import AccountSparkline from './AccountSparkline.vue'
import { fetchRecentTransactions } from '@/api/accounts'

const groupAccounts = ref([])
const MAX_ACCOUNTS_PER_GROUP = 5

const accountId = (account) => {
  if (!account) return ''
  const raw = account.account_id ?? account.id ?? ''
  if (raw === null || raw === undefined) return ''
  return typeof raw === 'number' ? String(raw) : raw
}

const normalizeAccount = (account) => {
  if (!account || typeof account !== 'object') return null
  const id = accountId(account)
  if (!id) return null
  return { ...account, id }
}

const normalizeAccounts = (list) => {
  if (!Array.isArray(list)) return []
  const seen = new Set()
  const normalized = []
  for (const entry of list) {
    const normalizedEntry = normalizeAccount(entry)
    if (!normalizedEntry) continue
    if (seen.has(normalizedEntry.id)) continue
    seen.add(normalizedEntry.id)
    normalized.push(normalizedEntry)
  }
  return normalized
}

function accountsMatch(a, b) {
  if (!Array.isArray(a) || !Array.isArray(b)) return false
  if (a.length !== b.length) return false
  return a.every((item, idx) => accountId(item) === accountId(b[idx]))
}

const props = defineProps({
  accountSubtype: { type: String, default: '' },
  useSpectrum: { type: Boolean, default: false },
  isEditingGroups: { type: Boolean, default: false },
})

// fetch accounts generically for potential group management
const { accounts: allAccounts } = useTopAccounts()
const accounts = allAccounts
const {
  groups,
  activeGroupId,
  createGroup,
  updateGroup,
  removeGroup,
  reorderGroups,
  setActiveGroup: persistActiveGroup,
  addAccountToGroup,
  removeAccountFromGroup,
  syncGroupAccounts,
  offlineMode,
} = useAccountGroups()

// Details dropdown state
const openAccountId = ref(null)
const recentTxs = reactive({})

let syncingFromActive = false
let syncingToActive = false

/** Toggle details dropdown for an account and load recent transactions */
function toggleDetails(accountId, event) {
  if (!accountId) return
  const switchingAccount = openAccountId.value !== accountId
  openAccountId.value = openAccountId.value === accountId ? null : accountId
  if (switchingAccount && showGroupMenu.value) {
    showGroupMenu.value = false
  }
  // Ensure the originating row retains focus for accessibility
  event?.currentTarget?.focus()
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
const groupMenuRef = ref(null)
const groupMenuButtonRef = ref(null)
const editingGroupId = ref(null)
const activeGroupNameDraft = ref('')
const isRenamingTitle = ref(false)
// Maximum allowed characters for group names, including ellipsis when truncated.
const MAX_GROUP_NAME_LENGTH = 30
const isEditingGroups = ref(props.isEditingGroups)
const groupDropdownClasses = computed(() => ({
  'bs-group-btn': true,
  'gradient-toggle-btn': true,
  'is-active': showGroupMenu.value || isEditingGroups.value,
}))
watch(
  () => props.isEditingGroups,
  (val) => {
    isEditingGroups.value = val
    if (!val) {
      closeGroupMenu()
    }
  },
)

// Currently active/persisted group from store
const activeGroup = computed(() => groups.value.find((g) => g.id === activeGroupId.value) || null)
// Fallback to the first available group until an active one is set
const effectiveGroup = computed(() => activeGroup.value || groups.value[0] || null)

// Ensure a sensible default: select the first group when none is active
watch(
  groups,
  (list) => {
    if (!Array.isArray(list) || list.length === 0) return
    // If no active group yet, initialize to the first available one
    if (!activeGroupId.value) {
      setActiveGroup(list[0].id)
      return
    }
    // If the active group was removed, select the first available one
    if (!list.some((g) => g.id === activeGroupId.value)) {
      setActiveGroup(list[0].id)
    }
  },
  { immediate: true, deep: true },
)

// Close the dropdown any time the active group changes (e.g., on selection)
watch(
  () => activeGroupId.value,
  () => closeGroupMenu(),
)

// Keep local draggable list in sync with the effective group accounts
watch(
  () => effectiveGroup.value?.accounts,
  (val) => {
    if (syncingToActive) return
    const normalized = normalizeAccounts(val)
    if (accountsMatch(normalized, groupAccounts.value)) return
    syncingFromActive = true
    groupAccounts.value = normalized
    // Close open details and prune cached txns when the active group changes underneath us
    if (
      openAccountId.value &&
      !normalized.some((acct) => accountId(acct) === openAccountId.value)
    ) {
      openAccountId.value = null
    }
    for (const key of Object.keys(recentTxs)) {
      if (!normalized.some((acct) => accountId(acct) === key)) {
        delete recentTxs[key]
      }
    }
    syncingFromActive = false
  },
  { immediate: true, deep: true },
)

watch(
  groupAccounts,
  (val) => {
    if (syncingFromActive || !activeGroup.value) return
    syncingToActive = true
    const normalized = normalizeAccounts(val)
    if (accountsMatch(normalized, activeGroup.value?.accounts || [])) {
      syncingToActive = false
      return
    }
    if (!Array.isArray(activeGroup.value.accounts)) {
      activeGroup.value.accounts = []
    }
    activeGroup.value.accounts.splice(0, activeGroup.value.accounts.length, ...normalized)
    syncingToActive = false
  },
  { deep: true },
)

const groupAccent = computed(() => effectiveGroup.value?.accent || 'var(--color-accent-cyan)')

// As an extra safeguard, ensure a default selection on mount
onMounted(() => {
  if (!activeGroupId.value && groups.value.length > 0) {
    setActiveGroup(groups.value[0].id)
  }
})

// Close group dropdown when clicking outside of it
function containsTarget(el, target) {
  if (!el || !target) return false
  if (typeof Node !== 'undefined' && !(target instanceof Node)) {
    return false
  }
  return typeof el.contains === 'function' && el.contains(target)
}

function closeGroupMenu(focusButton = false, force = false) {
  if (!showGroupMenu.value && !force) return
  showGroupMenu.value = false
  if (focusButton) {
    groupMenuButtonRef.value?.focus?.()
  }
}

function onDocumentClick(e) {
  if (!showGroupMenu.value) return
  const target = e?.target ?? null
  const insideButton = containsTarget(groupMenuButtonRef.value, target)
  const insideMenu = containsTarget(groupMenuRef.value, target)
  if (!insideButton && !insideMenu) {
    closeGroupMenu()
  }
}

function onDocumentKeydown(e) {
  if (!showGroupMenu.value) return
  if (e.key === 'Escape' || e.key === 'Esc') {
    closeGroupMenu(true)
  }
}

function addDropdownListeners() {
  if (typeof document === 'undefined') return
  document.addEventListener('click', onDocumentClick, true)
  document.addEventListener('pointerdown', onDocumentClick, true)
  document.addEventListener('keydown', onDocumentKeydown, true)
}

function removeDropdownListeners() {
  if (typeof document === 'undefined') return
  document.removeEventListener('click', onDocumentClick, true)
  document.removeEventListener('pointerdown', onDocumentClick, true)
  document.removeEventListener('keydown', onDocumentKeydown, true)
}

watch(
  showGroupMenu,
  (open) => {
    if (open) {
      addDropdownListeners()
    } else {
      removeDropdownListeners()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  removeDropdownListeners()
})

const spectrum = [
  'var(--color-accent-cyan)',
  'var(--color-accent-yellow)',
  'var(--color-accent-red)',
  'var(--color-accent-blue)',
]

/**
 * Resolve the first valid numeric account balance using the preferred precedence order.
 *
 * @param {object} account - Account payload containing one or more balance fields.
 * @returns {number} First valid numeric value, or 0 when no valid balance is available.
 */
function resolveAccountBalance(account) {
  if (!account || typeof account !== 'object') return 0
  const candidates = [
    account.adjusted_balance,
    account.balance,
    account.balances?.current,
    account.balances?.available,
  ]
  for (const candidate of candidates) {
    const numeric = Number(candidate)
    if (Number.isFinite(numeric)) {
      return numeric
    }
  }
  return 0
}

/**
 * Determine whether an account should be treated as a credit account for balance styling.
 * Credit accounts should always show negative (red) balance styling regardless of amount sign.
 */
function isCreditAccount(account) {
  if (!account || typeof account !== 'object') return false
  const creditHints = [account.subtype, account.type, account.account_type]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())
  return creditHints.some((value) => value.includes('credit'))
}

/**
 * Resolve a credit limit from the account payload, guarding against invalid values.
 */
function getCreditLimit(account) {
  if (!account || typeof account !== 'object') return null
  const limitValue = account.limit ?? account.credit_limit ?? account.balances?.limit
  if (limitValue === null || limitValue === undefined) return null
  const limitNumber = Number(limitValue)
  if (!Number.isFinite(limitNumber) || limitNumber <= 0) return null
  return limitNumber
}

/**
 * Build credit utilization metadata for display, or return null when unavailable.
 */
function creditUtilization(account) {
  if (!isCreditAccount(account)) return null
  const limit = getCreditLimit(account)
  if (!limit) return null
  const rawBalance =
    account?.adjusted_balance ?? account?.balances?.current ?? account?.balances?.balance
  const balanceNumber = Number(rawBalance)
  // Use absolute balance for utilization, since credit balances may be negative.
  const balance = Number.isFinite(balanceNumber) ? Math.abs(balanceNumber) : 0
  const utilizationRaw = (balance / limit) * 100
  if (!Number.isFinite(utilizationRaw)) return null
  const percent = Math.round(utilizationRaw)
  // Clamp the bar fill so overflow balances still render within the indicator.
  const barPercent = Math.min(Math.max(utilizationRaw, 0), 100)
  return {
    balance,
    limit,
    percent,
    barPercent,
    balanceLabel: formatCurrency(balance),
    limitLabel: formatCurrency(limit),
    percentLabel: `${percent}%`,
  }
}

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

/**
 * Provide balance styling based on account type and balance polarity.
 * Credit accounts always render as negative (red) regardless of balance sign.
 *
 * @param {object} account - Account payload containing balance metadata.
 * @returns {string} CSS class to apply to the account balance.
 */
function balanceClass(account) {
  const balance = resolveAccountBalance(account)
  if (isCreditAccount(account)) {
    // Credit accounts represent liabilities, so always render them as negative (red).
    return 'bs-balance-neg'
  }
  if (balance > 0) {
    return 'bs-balance-pos'
  }
  if (balance < 0) {
    return 'bs-balance-neg'
  }
  return ''
}

function resolveCreditLimit(account) {
  if (!account || typeof account !== 'object') return null
  const current = Math.abs(
    Number(
      account?.balances?.current ??
        account?.balance ??
        account?.adjusted_balance ??
        account?.balances?.available ??
        0,
    ),
  )
  const candidates = [
    account?.limit,
    account?.credit_limit,
    account?.creditLimit,
    account?.balances?.limit,
    account?.balances?.credit_limit,
  ]
  for (const candidate of candidates) {
    const numeric = Number(candidate)
    if (!Number.isNaN(numeric) && numeric > 0) {
      return numeric
    }
  }
  const available = Number(account?.balances?.available)
  if (!Number.isNaN(available) && available > 0 && current >= 0) {
    return available + current
  }
  return null
}

function resolveUtilization(account) {
  if (!isCreditAccount(account)) return null
  const limit = resolveCreditLimit(account)
  if (!limit || limit <= 0) return null
  const balance = Math.abs(
    Number(account?.balance ?? account?.adjusted_balance ?? account?.balances?.current ?? 0),
  )
  if (Number.isNaN(balance)) return null
  const pct = (balance / limit) * 100
  return { pct, balance, limit }
}

function showUtilization(account) {
  return Boolean(resolveUtilization(account))
}

function formatUtilization(account) {
  const utilization = resolveUtilization(account)
  if (!utilization) return ''
  return `${utilization.pct.toFixed(0)}%`
}

function utilizationWidth(account) {
  const utilization = resolveUtilization(account)
  if (!utilization) return '0%'
  const clamped = Math.min(Math.max(utilization.pct, 0), 100)
  return `${clamped.toFixed(0)}%`
}

function setActiveGroup(id) {
  persistActiveGroup(id)
}

function toggleGroupMenu() {
  showGroupMenu.value = !showGroupMenu.value
}

function selectGroup(id) {
  if (id) {
    setActiveGroup(id)
    const picked = groups.value.find((g) => g.id === id)
    groupAccounts.value = normalizeAccounts(picked?.accounts || [])
    openAccountId.value = null
    isRenamingTitle.value = false
    activeGroupNameDraft.value = ''
  }
  closeGroupMenu(true, true)
}

function persistGroupOrder() {
  reorderGroups(groups.value)
}

const emit = defineEmits(['update:isEditingGroups'])

/**
 * Reset transient editing UI state including focused group/tab inputs
 * and any pending account selector choices.
 */
function resetEditingUi() {
  editingGroupId.value = null
  showAccountSelector.value = false
  selectedAccountId.value = ''
  isRenamingTitle.value = false
  activeGroupNameDraft.value = ''
}

function toggleEditGroups(force) {
  const nextState = typeof force === 'boolean' ? force : !isEditingGroups.value
  if (!nextState) {
    resetEditingUi()
  }
  if (isEditingGroups.value !== nextState) {
    isEditingGroups.value = nextState
    emit('update:isEditingGroups', nextState)
  }
  showGroupMenu.value = false
}

function finishEditingSession(event) {
  if (event?.preventDefault) {
    event.preventDefault()
  }
  if (!isEditingGroups.value) {
    showGroupMenu.value = false
    event?.currentTarget?.blur?.()
    return
  }
  persistGroupOrder()
  persistAccountOrder()
  toggleEditGroups(false)
  event?.currentTarget?.blur?.()
}

/** Enable editing for a group tab when editing mode is active */
function startEdit(id) {
  if (!isEditingGroups.value) return
  editingGroupId.value = id
}

function startTitleEdit() {
  if (!isEditingGroups.value || !activeGroup.value) return
  activeGroupNameDraft.value = activeGroup.value.name || ''
  editingGroupId.value = activeGroupId.value
  isRenamingTitle.value = true
  // focus handled by input mount
}

function finishActiveTitleEdit() {
  if (!isEditingGroups.value || !activeGroup.value) {
    isRenamingTitle.value = false
    return
  }
  const trimmed = (activeGroupNameDraft.value || '').trim()
  if (!trimmed) {
    activeGroupNameDraft.value = activeGroup.value.name || ''
    isRenamingTitle.value = false
    editingGroupId.value = null
    return
  }
  activeGroup.value.name =
    trimmed.length > MAX_GROUP_NAME_LENGTH
      ? `${trimmed.slice(0, MAX_GROUP_NAME_LENGTH - 1)}…`
      : trimmed
  finishEdit(activeGroup.value)
  activeGroupNameDraft.value = ''
  isRenamingTitle.value = false
  editingGroupId.value = null
}

/**
 * Disable editing and persist the group name.
 * Truncates names longer than MAX_GROUP_NAME_LENGTH characters (including ellipsis).
 */
function finishEdit(group) {
  if (!group) return
  if (!isEditingGroups.value && editingGroupId.value !== group.id) {
    return
  }
  editingGroupId.value = null
  if (!group.name) {
    editingGroupId.value = group.id
    return
  }
  if (group.name.length > MAX_GROUP_NAME_LENGTH) {
    group.name = `${group.name.slice(0, MAX_GROUP_NAME_LENGTH - 1)}…`
  }
  updateGroup(group.id, { name: group.name })
}

/** Create a new group and start editing its name */
function addGroup() {
  const id = createGroup()
  selectGroup(id)
  editingGroupId.value = id
}

const activeAccounts = computed(() => groupAccounts.value)
const availableAccounts = computed(() => {
  const taken = new Set(activeAccounts.value.map((acct) => accountId(acct)))
  return normalizeAccounts(allAccounts.value)
    .filter((acct) => !taken.has(accountId(acct)))
    .sort((a, b) => {
      const aLabel = `${a.institution_name || ''} ${a.name || ''}`.trim().toLowerCase()
      const bLabel = `${b.institution_name || ''} ${b.name || ''}`.trim().toLowerCase()
      return aLabel.localeCompare(bLabel)
    })
})
/** Default preview accounts rendered when the user has not yet configured a group. */
const fallbackAccounts = computed(() => {
  if (groupAccounts.value.length) return []
  const normalized = normalizeAccounts(allAccounts.value)
  return normalized.slice(0, MAX_ACCOUNTS_PER_GROUP)
})
const visibleAccounts = computed(() =>
  activeAccounts.value.length ? activeAccounts.value : fallbackAccounts.value,
)
const hasConfiguredAccounts = computed(() => groupAccounts.value.length > 0)
const showAccountSelector = ref(false)
const selectedAccountId = ref('')

watch(
  activeGroupId,
  () => {
    openAccountId.value = null
    showAccountSelector.value = false
    selectedAccountId.value = ''
    isRenamingTitle.value = false
    activeGroupNameDraft.value = ''
  },
  { flush: 'post' },
)

watch(
  isEditingGroups,
  (editing) => {
    if (editing) {
      openAccountId.value = null
    } else {
      showAccountSelector.value = false
      selectedAccountId.value = ''
    }
  },
  { flush: 'post' },
)

function startAddAccount() {
  if (!isEditingGroups.value && activeAccounts.value.length > 0) return
  if (activeAccounts.value.length >= MAX_ACCOUNTS_PER_GROUP) return
  selectedAccountId.value = ''
  showAccountSelector.value = true
}

function confirmAddAccount() {
  if (!selectedAccountId.value) {
    showAccountSelector.value = false
    return
  }
  const acct = availableAccounts.value.find((a) => accountId(a) === selectedAccountId.value)
  if (acct) {
    addAccountToGroup(activeGroupId.value, acct)
  }
  showAccountSelector.value = false
  selectedAccountId.value = ''
}

function persistAccountOrder() {
  if (!activeGroupId.value) return
  syncGroupAccounts(activeGroupId.value, groupAccounts.value)
}

function removeAccount(id) {
  if (removeAccountFromGroup(activeGroupId.value, id)) {
    groupAccounts.value = groupAccounts.value.filter((acct) => accountId(acct) !== id)
    if (openAccountId.value === id) {
      openAccountId.value = null
    }
    if (id in recentTxs) {
      delete recentTxs[id]
    }
  }
}

const visibleTotal = computed(() =>
  visibleAccounts.value.reduce((sum, account) => sum + resolveAccountBalance(account), 0),
)

const totalValueClass = computed(() => {
  const total = Number(visibleTotal.value) || 0
  if (total > 0) return 'bs-total-pos'
  if (total < 0) return 'bs-total-neg'
  return 'bs-total-neutral'
})

/**
 * Format a currency value without accounting-style parentheses.
 */

function formatCurrency(val) {
  const formatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  if (typeof val !== 'number') return ''
  return formatter.format(val)
}

/**
 * Format a currency value using accounting-style parentheses for negatives.
 */

const format = (val) => {
  if (typeof val !== 'number') return ''
  if (val < 0) {
    return `(${formatCurrency(Math.abs(val))})`
  }
  return formatCurrency(val)
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

function formatShortDate(s) {
  if (!s) return ''
  // Accept common ISO formats and fallback to raw if invalid
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return s
  try {
    return new Intl.DateTimeFormat('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: '2-digit',
    }).format(d)
  } catch {
    return s
  }
}

function amountClass(val) {
  const num = Number(val) || 0
  if (num < 0) return 'bs-amt-neg'
  if (num > 0) return 'bs-amt-pos'
  return ''
}

defineExpose({
  accounts,
  allAccounts: accounts,
  groups,
  activeGroupId,
  groupAccounts,
  groupAccent,
  isEditingGroups,
  showGroupMenu,
  finishEditingSession,
  selectedAccountId,
  showAccountSelector,
  startAddAccount,
  confirmAddAccount,
  selectGroup,
})
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
  padding: 0.65rem 1rem;
  border-left: 4px solid var(--accent);
  border-radius: 0 0 0.6rem 0.6rem;
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

.bs-amt-pos {
  color: var(--color-accent-cyan);
}
.bs-amt-neg {
  color: var(--color-accent-red);
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

.bs-editing {
  box-sizing: border-box;
  position: relative;
  border-radius: 1.3rem;
  padding: clamp(0.75rem, 1vw + 0.5rem, 1.2rem);
  background: linear-gradient(135deg, rgba(12, 23, 52, 0.92), rgba(12, 23, 52, 0.78));
  box-shadow:
    0 24px 48px rgba(12, 23, 52, 0.28),
    0 0 0 2px var(--accent, var(--color-accent-cyan));
  transition: box-shadow 0.25s ease;
}

.bs-editing:hover {
  box-shadow:
    0 30px 60px rgba(12, 23, 52, 0.32),
    0 0 0 2px var(--accent, var(--color-accent-cyan));
}

.bs-editing-banner {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  border: 1px dashed var(--accent, var(--color-accent-cyan));
  color: var(--accent, var(--color-accent-cyan));
  background: color-mix(in srgb, var(--accent, var(--color-accent-cyan)) 15%, transparent);
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
}

.bs-editing-icon {
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
}

.bs-editing-title {
  font-weight: 700;
  letter-spacing: 0.01em;
  text-transform: uppercase;
  font-size: 0.8rem;
}

.bs-editing-subtitle {
  font-size: 0.75rem;
  opacity: 0.8;
}

.bs-editing .bs-tab {
  border-style: dashed;
  border-color: var(--accent, var(--color-accent-cyan));
  background: rgba(12, 23, 52, 0.82);
  color: var(--accent, var(--color-accent-cyan));
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.05),
    0 12px 26px rgba(12, 23, 52, 0.35);
}

.dark .bs-editing .bs-tab {
  background: rgba(12, 23, 52, 0.55);
}

.bs-editing .bs-tab-add {
  font-weight: 700;
}

.bs-editing .bs-tab-input {
  background: transparent;
  color: var(--accent, var(--color-accent-cyan));
  font-weight: 700;
  letter-spacing: 0.01em;
}

.bs-editing .bs-tab-input::placeholder {
  color: var(--accent, var(--color-accent-cyan));
  opacity: 0.55;
}

.bs-editing .bs-tab-input:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--accent, var(--color-accent-cyan));
  border-radius: 0.6rem;
}

.bs-editing .bs-tab-handle,
.bs-editing .bs-tab-delete {
  color: var(--accent, var(--color-accent-cyan));
}

.bs-editing .bs-tab-delete:hover,
.bs-editing .bs-tab-delete:focus-visible {
  color: var(--color-accent-red);
}

.bs-editing .bs-group-input {
  background: rgba(12, 23, 52, 0.85);
  border: 1.6px dashed var(--accent, var(--color-accent-cyan));
  color: var(--accent, var(--color-accent-cyan));
  box-shadow: 0 12px 26px rgba(12, 23, 52, 0.35);
}

.bs-editing .bs-group-item-active {
  background: rgba(12, 23, 52, 0.85);
  border-left: 3px solid var(--accent, var(--color-accent-cyan));
}

.bs-editing .bs-account-delete {
  color: var(--accent, var(--color-accent-cyan));
}

.bs-editing .bs-row {
  border-style: dashed;
  box-shadow:
    0 8px 24px rgba(12, 23, 52, 0.35),
    inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.bs-editing .bs-add-placeholder {
  border-style: dashed;
  color: var(--accent, var(--color-accent-cyan));
}

.bs-toggle-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.7rem;
  margin-bottom: 1.1rem;
  background: transparent;
  border-radius: 1rem 1rem 0 0;
  flex-wrap: wrap;
}

.bs-tabs-scroll {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  overflow: hidden;
  min-width: 0;
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
  display: flex;
  align-items: center;
  gap: 0.25rem;
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

.bs-tab-handle {
  cursor: move;
  width: 1rem;
  height: 1rem;
}

.bs-tab-delete {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: color 0.2s ease;
}

.bs-account-delete {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: color 0.2s ease;
}

.bs-tab-delete:hover,
.bs-tab-delete:focus-visible,
.bs-account-delete:hover,
.bs-account-delete:focus-visible {
  color: var(--color-accent-red);
}

.bs-add-account {
  list-style: none;
}

.bs-add-placeholder {
  opacity: 0.8;
  color: var(--color-text-muted);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  border: 2px dashed var(--accent, var(--color-accent-cyan));
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.bs-add-placeholder:hover,
.bs-add-placeholder:focus-visible {
  background: var(--accent, var(--color-accent-cyan));
  color: var(--color-bg-dark);
}

.bs-add-icon {
  width: 1rem;
  height: 1rem;
  color: var(--accent, var(--color-accent-cyan));
}

.bs-add-account.bs-disabled {
  opacity: 0.5;
  pointer-events: none;
}

.bs-add-select {
  width: 100%;
  padding: 0.25rem;
  border-radius: 0.25rem;
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

.bs-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.bs-group-banner {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent) 16%, transparent), transparent),
    color-mix(in srgb, var(--color-bg-sec) 80%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent);
  border-radius: 0.9rem;
  padding: 0.75rem 0.9rem;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
}

.bs-group-title {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.bs-group-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-light);
}

.bs-group-name.muted {
  color: var(--color-text-muted);
}

.bs-title-field {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 0.6rem;
  background: color-mix(in srgb, var(--color-bg-sec) 80%, transparent);
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease;
}

.bs-title-field.is-active {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, var(--color-bg-sec));
}

.bs-title-input {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-light);
  background: var(--color-bg-sec);
  border: 1px solid var(--accent);
  border-radius: 0.4rem;
  padding: 0.25rem 0.5rem;
  min-width: 9rem;
}

.bs-rename-btn {
  font-size: 0.8rem;
  font-weight: 600;
  padding: 0.25rem 0.6rem;
  border-radius: 0.5rem;
  border: 1px solid var(--accent);
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  cursor: pointer;
}

.bs-rename-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 35%, transparent);
}

.bs-banner-meta {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.bs-banner-label {
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bs-banner-value {
  font-weight: 700;
  font-size: 1.15rem;
  font-variant-numeric: tabular-nums;
  color: color-mix(in srgb, var(--accent) 70%, var(--color-text-light));
}

.bs-total-pos {
  color: var(--color-accent-cyan);
}

.bs-total-neg {
  color: var(--color-accent-red);
}

.bs-total-neutral {
  color: var(--color-text-muted);
}

.bs-editing-chip {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 60%, transparent);
  border-radius: 999px;
  padding: 0.15rem 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.bs-editing-footer {
  margin-top: 0.75rem;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 900px) {
  .bs-toggle-row {
    row-gap: 0.5rem;
  }

  .bs-tabs-scroll {
    flex-basis: 100%;
  }

  .bs-group-dropdown {
    margin-left: 0;
    flex-basis: 100%;
    display: flex;
    justify-content: flex-end;
  }
}

.bs-group-btn {
  padding: 0.35rem 0.9rem;
  border-radius: 0.65rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.bs-group-btn:focus-visible {
  outline: none;
}

.bs-done-btn {
  padding: 0.35rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
}

.bs-done-btn:focus-visible {
  outline: none;
}

.bs-nav-btn {
  padding: 0.35rem 0.65rem;
  border-radius: 0.65rem;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bs-nav-btn:focus-visible {
  outline: none;
}

.bs-nav-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.bs-group-menu {
  position: absolute;
  right: 0;
  margin-top: 0.2rem;
  background: var(--color-bg-sec);
  border: 1px solid var(--accent);
  border-radius: 0.5rem;
  /* Ensure the dropdown sits above draggable rows */
  z-index: 1000;
  display: flex;
  flex-direction: column;
  min-width: 8rem;
  padding: 0.2rem 0;
}

.bs-group-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0 0.25rem;
}

.bs-group-handle {
  width: 1.1rem;
  height: 1.1rem;
  color: var(--accent);
  cursor: grab;
  flex-shrink: 0;
  opacity: 0.75;
}

.bs-group-delete {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 0.15rem;
  border-radius: 0.35rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.bs-group-delete:hover,
.bs-group-delete:focus-visible {
  color: var(--color-accent-red);
  outline: none;
}

/* Establish a positioning context for the absolute menu */
.bs-group-dropdown {
  position: relative;
}

/* Inline group input when editing from dropdown */
.bs-group-input {
  width: 100%;
  padding: 0.35rem 0.6rem;
  border-radius: 0.35rem;
  border: 1px solid var(--accent);
  background: var(--color-bg-dark);
  color: var(--color-text-light);
  font-size: 0.9rem;
}

/* Action button in dropdown (Edit/Done) */
.bs-group-action {
  font-weight: 700;
  justify-content: center;
  border-top: 1px solid var(--accent);
}

.bs-group-item {
  padding: 0.4rem 0.8rem;
  background: transparent;
  color: var(--color-text-light);
  border: none;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  transition:
    background-color 0.2s ease,
    color 0.2s ease;
}

.bs-group-item:hover,
.bs-group-item:focus-visible,
.bs-group-item.is-active,
.bs-group-item-active {
  background: var(--accent);
  color: var(--color-bg-dark);
}

.bs-group-item.is-active,
.bs-group-item-active {
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--accent);
}

.bs-group-item:active {
  transform: translateY(1px);
}

.bs-group-check {
  width: 0.9rem;
  height: 0.9rem;
  color: var(--accent);
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

.bs-list--static {
  pointer-events: none;
}

.bs-list--static .bs-row--static {
  pointer-events: auto;
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

.bs-row--static {
  cursor: pointer;
}

.bs-static-spacer {
  width: 1rem;
  height: 1rem;
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
  width: 96px;
  height: 36px;
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

.bs-utilization {
  margin-top: 0.2rem;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.bs-utilization-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.35rem;
  font-weight: 600;
}

.bs-utilization-label {
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.bs-utilization-percent {
  font-size: 0.65rem;
  color: var(--color-accent-red);
}

.bs-utilization-bar {
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg-sec) 65%, transparent);
  overflow: hidden;
}

.bs-utilization-fill {
  height: 100%;
  background: var(--color-accent-red);
  border-radius: inherit;
}

.bs-utilization-text {
  font-size: 0.68rem;
  color: var(--color-text-light);
  opacity: 0.85;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bs-amount-section {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.35rem;
  height: 100%;
  z-index: 2;
}

.bs-amount-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.15rem;
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
  color: var(--color-text-light);
}

.bs-utilization {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.68rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.bs-utilization-label {
  font-weight: 600;
}

.bs-utilization-value {
  font-weight: 700;
  color: var(--color-text-light);
}

.bs-utilization-bar {
  width: 54px;
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-bg-dark) 80%, transparent);
  overflow: hidden;
}

.bs-utilization-fill {
  display: block;
  height: 100%;
  background: var(--color-accent-red);
  border-radius: inherit;
}

.bs-balance-pos {
  color: var(--color-accent-green);
}

.bs-balance-neg {
  color: var(--color-accent-red);
}

.bs-empty {
  color: var(--color-text-muted);
  font-style: italic;
  padding: 1.2rem 0 0.7rem 0;
  text-align: center;
  font-size: 1.01rem;
}

.bs-fallback {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.bs-fallback-note {
  margin: 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  text-align: left;
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

.list-fade-enter-active,
.list-fade-leave-active {
  transition: all 0.2s ease;
}

.list-fade-enter-from,
.list-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
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
    font-size: var(--font-size-sm);
  }

  .bs-tabs-scroll {
    overflow-x: auto;
    overflow-y: hidden;
  }

  .bs-tab-list {
    flex-wrap: nowrap;
    width: max-content;
  }

  .bs-add-select {
    font-size: 0.85rem;
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

  .bs-utilization {
    font-size: 0.62rem;
  }

  .bs-utilization-text {
    font-size: 0.62rem;
  }

  .bs-utilization-bar {
    height: 3px;
  }
}
</style>
