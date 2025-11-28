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
    <Transition name="fade-in">
      <div
        v-if="isEditingGroups"
        class="bs-editing-banner"
        :style="{ '--accent': groupAccent }"
        role="status"
        aria-live="polite"
      >
        <span class="i-carbon-edit bs-editing-icon" aria-hidden="true"></span>
        <div class="bs-editing-copy">
          <p class="bs-editing-title">Editing mode enabled</p>
          <p class="bs-editing-subtitle">
            Drag to reorder, rename groups inline, and use the icons to remove accounts.
          </p>
        </div>
      </div>
    </Transition>
    <!-- Group Tabs -->
    <div class="bs-toggle-row">
      <div class="bs-tabs-scroll">
        <button
          v-if="!isEditingGroups && groups.length > 3"
          class="bs-nav-btn gradient-toggle-btn"
          @click="shiftWindow(-1)"
          :disabled="visibleGroupIndex === 0"
          aria-label="Previous group"
        >
          &lt;
        </button>
        <Draggable
          v-if="isEditingGroups"
          v-model="groups"
          item-key="id"
          handle=".bs-tab-handle"
          tag="div"
          class="bs-tab-list"
          @end="persistGroupOrder"
        >
          <template #item="{ element: g }">
            <div
              :key="g.id"
              :class="['bs-tab', activeGroupId === g.id && 'bs-tab-active', 'bs-tab-' + g.id]"
            >
              <GripVertical class="bs-tab-handle" />
              <input
                v-model="g.name"
                class="bs-tab-input"
                maxlength="30"
                @blur="finishEdit(g)"
                @keyup.enter="finishEdit(g)"
              />
              <X class="bs-tab-delete" @click.stop="removeGroup(g.id)" />
            </div>
          </template>
          <template #footer>
            <button
              key="add-group"
              class="bs-tab bs-tab-add"
              @click="addGroup"
              aria-label="Add group"
            >
              +
            </button>
          </template>
        </Draggable>
        <TransitionGroup v-else name="fade-in" tag="div" class="bs-tab-list">
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
              maxlength="30"
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
        </TransitionGroup>

        <button
          v-if="groups.length > 3"
          class="bs-nav-btn gradient-toggle-btn"
          @click="shiftWindow(1)"
          :disabled="visibleGroupIndex + 3 >= groups.length"
          aria-label="Next group"
        >
          &gt;
        </button>
      </div>

      <!-- Group Dropdown -->
      <div class="bs-group-dropdown" :style="{ '--accent': groupAccent }">
        <button
          ref="groupMenuButtonRef"
          type="button"
          :class="groupDropdownClasses"
          @click="toggleGroupMenu"
          aria-label="Select account group"
        >
          {{ effectiveGroup ? effectiveGroup.name : 'Select group' }} ▾
        </button>
        <Transition name="slide-down">
          <ul v-if="showGroupMenu" ref="groupMenuRef" class="bs-group-menu">
            <li v-for="g in groups" :key="g.id">
              <template v-if="isEditingGroups">
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
                >
                  <Check v-if="g.id === activeGroupId" class="bs-group-check" />
                  {{ g.name || '(unnamed)' }}
                </button>
              </template>
            </li>
            <li v-if="!isEditingGroups">
              <button
                type="button"
                class="bs-group-item bs-group-action gradient-toggle-btn"
                @click="toggleEditGroups"
                aria-label="Edit account groups"
              >
                Edit
              </button>
            </li>
          </ul>
        </Transition>
      </div>

      <button
        v-if="isEditingGroups"
        type="button"
        class="bs-done-btn gradient-toggle-btn"
        @click="finishEditingSession"
        aria-label="Finish editing account groups"
      >
        Done
      </button>
    </div>

    <!-- Render draggable without container Transition to avoid DOM detachment issues -->
    <Draggable
      v-if="effectiveGroup && (isEditingGroups || hasConfiguredAccounts)"
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
            </div>
            <div class="bs-sparkline">
              <AccountSparkline :account-id="accountId(account)" />
            </div>
            <div class="bs-amount-section">
              <span class="bs-amount">{{ format(account.adjusted_balance) }}</span>
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
            </div>
            <div class="bs-sparkline">
              <AccountSparkline :account-id="accountId(account)" />
            </div>
            <div class="bs-amount-section">
              <span class="bs-amount">{{ format(account.adjusted_balance) }}</span>
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
  </div>
</template>

<!-- liabilities section removed -->

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
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

const props = defineProps({
  accountSubtype: { type: String, default: '' },
  useSpectrum: { type: Boolean, default: false },
  isEditingGroups: { type: Boolean, default: false },
})

// fetch accounts generically for potential group management
const { accounts: allAccounts } = useTopAccounts()
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
  openAccountId.value = openAccountId.value === accountId ? null : accountId
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

// Keep local draggable list in sync with the effective group accounts
watch(
  () => effectiveGroup.value?.accounts,
  (val) => {
    if (syncingToActive) return
    syncingFromActive = true
    const normalized = normalizeAccounts(val)
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

function onDocumentClick(e) {
  if (!showGroupMenu.value) return
  const target = e?.target ?? null
  const insideButton = containsTarget(groupMenuButtonRef.value, target)
  const insideMenu = containsTarget(groupMenuRef.value, target)
  if (!insideButton && !insideMenu) {
    showGroupMenu.value = false
  }
}

function onDocumentKeydown(e) {
  if (!showGroupMenu.value) return
  if (e.key === 'Escape' || e.key === 'Esc') {
    showGroupMenu.value = false
    groupMenuButtonRef.value?.focus?.()
  }
}

watch(
  showGroupMenu,
  (open) => {
    if (typeof document === 'undefined') return
    if (open) {
      document.addEventListener('click', onDocumentClick, true)
      document.addEventListener('keydown', onDocumentKeydown, true)
    } else {
      document.removeEventListener('click', onDocumentClick, true)
      document.removeEventListener('keydown', onDocumentKeydown, true)
    }
  },
  { immediate: true },
)

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
  persistActiveGroup(id)
}

function toggleGroupMenu() {
  showGroupMenu.value = !showGroupMenu.value
}

function selectGroup(id) {
  if (id) {
    setActiveGroup(id)
  }
  showGroupMenu.value = false
  groupMenuButtonRef.value?.focus?.()
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
const hasConfiguredAccounts = computed(() => groupAccounts.value.length > 0)
const showAccountSelector = ref(false)
const selectedAccountId = ref('')

watch(
  activeGroupId,
  () => {
    const normalized = normalizeAccounts(effectiveGroup.value?.accounts || [])
    groupAccounts.value = normalized
    openAccountId.value = null
    showAccountSelector.value = false
    selectedAccountId.value = ''
  },
  { flush: 'post' },
)

watch(
  isEditingGroups,
  (editing) => {
    if (!editing) return
    openAccountId.value = null
  },
  { flush: 'post' },
)

function startAddAccount() {
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

const activeTotal = computed(() =>
  activeAccounts.value.reduce((sum, a) => sum + (Number(a.adjusted_balance) || 0), 0),
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
  accounts: allAccounts,
  allAccounts,
  groups,
  activeGroupId,
  groupAccounts,
  groupAccent,
  isEditingGroups,
  finishEditingSession,
  selectedAccountId,
  showAccountSelector,
  startAddAccount,
  confirmAddAccount,
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
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  margin-bottom: 1.1rem;
  border-radius: 0.9rem;
  border: 1.6px dashed var(--accent, var(--color-accent-cyan));
  color: var(--accent, var(--color-accent-cyan));
  background: linear-gradient(120deg, rgba(12, 23, 52, 0.92), rgba(12, 23, 52, 0.72));
  box-shadow: 0 18px 36px rgba(12, 23, 52, 0.32);
  overflow: hidden;
}

.bs-editing-banner::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--accent, var(--color-accent-cyan)) 0%, transparent 70%);
  opacity: 0.18;
  pointer-events: none;
}

.bs-editing-icon {
  font-size: 1.6rem;
  line-height: 1;
  flex-shrink: 0;
  filter: drop-shadow(0 4px 10px rgba(12, 23, 52, 0.4));
}

.bs-editing-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  color: var(--color-text-light);
}

.bs-editing-title {
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  font-size: 0.9rem;
}

.bs-editing-subtitle {
  font-size: 0.85rem;
  line-height: 1.4;
  opacity: 0.85;
  max-width: 32rem;
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
}
</style>
