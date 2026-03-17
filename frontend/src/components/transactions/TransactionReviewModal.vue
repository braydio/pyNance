<!--
  TransactionReviewModal.vue
  Batch review modal for approving or editing transactions without leaving the dashboard.
-->
<template>
  <transition name="modal-fade-slide">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm px-4 py-6"
      @click.self="emitClose"
    >
      <div
        class="review-modal-shell relative w-full max-w-4xl mx-auto p-0 rounded-2xl shadow-2xl bg-[var(--color-bg-sec)] border-2 border-[var(--color-accent-cyan)]/60 flex flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label="Review Transactions Modal"
      >
        <div
          class="flex items-center justify-between px-6 py-4 bg-[var(--color-bg-dark)] border-b-2 border-[var(--color-accent-cyan)]/50 shadow-lg"
        >
          <div class="flex flex-col gap-1">
            <h2 class="text-xl font-extrabold text-[var(--color-accent-cyan)] tracking-wide">
              Review Transactions
            </h2>
            <p
              class="review-shortcuts text-xs uppercase tracking-widest text-[var(--color-text-muted)]"
            >
              Use ← to edit, → to approve, 1-5 to jump fields, Enter to save
            </p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-sm text-[var(--color-text-muted)]">
              Batch {{ currentPage }} / {{ totalPages }} • {{ progressLabel }}
            </span>
            <button
              class="inline-flex items-center justify-center w-9 h-9 rounded-full text-[var(--color-accent-cyan)] border border-[var(--color-accent-cyan)]/40 hover:bg-[var(--color-accent-cyan)] hover:text-[var(--color-bg-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-accent-cyan)] transition"
              @click="emitClose"
              aria-label="Close Review Modal"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 6l12 12M6 18L18 6" />
              </svg>
            </button>
          </div>
        </div>

        <div class="flex-1 p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          <div v-if="isLoading" class="text-center text-[var(--color-text-muted)]">
            Loading transactions…
          </div>
          <div v-else-if="!currentTransaction && !batchComplete" class="text-center">
            <p class="text-[var(--color-text-muted)]">No transactions found for this range.</p>
            <div class="mt-4 flex justify-center gap-3">
              <button class="btn" @click="emitClose">Exit</button>
              <button class="btn" :disabled="!hasNextBatch" @click="startNextBatch">
                Start next batch
              </button>
            </div>
          </div>

          <div v-else-if="batchComplete" class="text-center space-y-4">
            <h3 class="text-2xl font-bold text-[var(--color-accent-cyan)]">Batch complete</h3>
            <p class="text-[var(--color-text-muted)]">You finished reviewing this batch.</p>
            <div class="flex justify-center gap-3">
              <button class="btn" @click="emitClose">Exit</button>
              <button class="btn" :disabled="!hasNextBatch" @click="startNextBatch">
                Start next batch
              </button>
            </div>
          </div>

          <div
            v-else
            class="rounded-2xl border border-[var(--divider)] bg-[var(--color-bg-dark)]/30 p-6 shadow-lg"
          >
            <div class="flex justify-between items-start mb-4">
              <div>
                <p class="text-sm text-[var(--color-text-muted)]">
                  {{ formattedDate(currentTransaction) }}
                </p>
                <h3 class="text-2xl font-bold text-[var(--color-accent-cyan)]">
                  {{ currentTransaction.description }}
                </h3>
              </div>
              <div class="text-right">
                <p
                  :class="[
                    'text-xl font-bold',
                    Number(currentTransaction.amount) < 0
                      ? 'text-[var(--color-accent-red)]'
                      : 'text-[var(--color-accent-green)]',
                  ]"
                >
                  {{ formatAmount(currentTransaction.amount) }}
                </p>
                <p class="text-sm text-[var(--color-text-muted)]">
                  {{ currentTransaction.account_name || 'Unknown account' }}
                </p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-for="field in displayFields" :key="field.key" class="review-field space-y-1">
                <label class="text-xs uppercase tracking-wide text-[var(--color-text-muted)]">{{
                  field.label
                }}</label>
                <p
                  v-if="isEditing && field.shortcutIndex"
                  class="text-[11px] uppercase tracking-wide text-[var(--color-text-muted)]"
                >
                  {{ field.shortcutIndex }}
                </p>
                <div v-if="isEditing" class="space-y-2">
                  <input
                    v-if="field.type === 'input'"
                    v-model="editBuffer[field.key]"
                    :ref="(element) => setEditInputRef(field.key, element)"
                    :type="field.inputType || 'text'"
                    :list="
                      field.key === 'category'
                        ? 'review-category-suggestions'
                        : field.key === 'tag'
                          ? 'review-tag-suggestions'
                          : undefined
                    "
                    class="input review-input w-full"
                  />
                  <input
                    v-else-if="field.type === 'date'"
                    v-model="editBuffer[field.key]"
                    :ref="(element) => setEditInputRef(field.key, element)"
                    type="date"
                    class="input review-input w-full"
                  />
                </div>
                <p v-else class="review-field-value font-semibold text-[var(--color-text-light)]">
                  {{ field.formatter ? field.formatter(currentTransaction) : field.value }}
                </p>
              </div>
            </div>

            <div class="review-actions flex flex-wrap gap-3 mt-6 items-center">
              <button class="btn btn-outline review-btn-secondary" @click="handleEditToggle">
                {{ isEditing ? 'Cancel' : 'Edit (←)' }}
              </button>
              <button class="btn review-btn-primary" @click="handleApprove">
                {{ isEditing ? 'Save & Next (→)' : 'Approve (→)' }}
              </button>
              <span class="text-sm text-[var(--color-text-muted)]">
                {{ progressLabel }} of {{ totalCount }} total
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </transition>
  <datalist id="review-category-suggestions">
    <option v-for="option in categorySuggestions" :key="option" :value="option" />
  </datalist>
  <datalist id="review-tag-suggestions">
    <option v-for="option in tagSuggestions" :key="option" :value="option" />
  </datalist>
  <div
    v-if="rulePrompt.visible"
    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 px-4"
    @click.self="resolveRulePrompt(false)"
  >
    <div
      class="w-full max-w-lg rounded-xl border border-[var(--divider)] bg-[var(--color-bg-sec)] p-5 shadow-2xl"
      role="dialog"
      aria-modal="true"
      aria-label="Save rule confirmation"
    >
      <h3 class="text-lg font-bold text-[var(--color-accent-cyan)]">
        Save rule for future matches?
      </h3>
      <p class="mt-3 text-sm text-[var(--color-text-muted)]">
        Always set <strong>{{ rulePrompt.field }}</strong> to
        <strong>"{{ rulePrompt.value }}"</strong> for
        <strong>{{ rulePrompt.description || 'this transaction description' }}</strong> in
        <strong>{{ rulePrompt.accountLabel }}</strong> at
        <strong>{{ rulePrompt.institutionLabel }}</strong
        >?
      </p>
      <div class="mt-5 flex justify-end gap-2">
        <button class="btn btn-outline" @click="resolveRulePrompt(false)">No, skip rule</button>
        <button class="btn" @click="resolveRulePrompt(true)">Yes, save rule</button>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Batch review modal for approving or editing transactions inline.
 *
 * Fetches transactions in groups of 10, supports keyboard navigation, and
 * offers in-context updates plus optional rule creation before advancing
 * through a batch.
 */
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import Fuse from 'fuse.js'
import { useToast } from 'vue-toastification'
import { useTransactions } from '@/composables/useTransactions'
import { createTransactionRule, fetchTagSuggestions, updateTransaction } from '@/api/transactions'
import { fetchCategoryTree } from '@/api/categories'
import { formatAmount } from '@/utils/format'

const props = defineProps({
  show: { type: Boolean, default: false },
  filters: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['close'])
const toast = useToast()

const BATCH_SIZE = 10
const CATEGORY_SUGGESTION_LIMIT = 12
const EDIT_SHORTCUT_FIELDS = ['category', 'tag', 'merchant_name', 'description', 'amount']
const filtersRef = computed(() => {
  const nextFilters = { ...(props.filters || {}) }
  if (!nextFilters.start_date) delete nextFilters.start_date
  if (!nextFilters.end_date) delete nextFilters.end_date
  if (typeof nextFilters.tags === 'string' && !nextFilters.tags.trim()) {
    delete nextFilters.tags
  }
  return nextFilters
})

const {
  paginatedTransactions,
  fetchTransactions: fetchBatch,
  currentPage,
  totalPages,
  totalCount,
  isLoading,
  setPage,
} = useTransactions(BATCH_SIZE, null, filtersRef)

const currentIndex = ref(0)
const editingTransactionId = ref('')
const editBuffer = ref({})
const batchComplete = ref(false)
const categoryOptions = ref([])
const tagOptions = ref([])
const editInputRefs = ref({})
const rulePrompt = ref({
  visible: false,
  field: '',
  value: '',
  description: '',
  accountLabel: 'this account',
  institutionLabel: 'this institution',
})
let pendingRulePromptResolver = null

const hasNextBatch = computed(() => currentPage.value < totalPages.value)

const currentTransaction = computed(() => paginatedTransactions.value?.[currentIndex.value] ?? null)

const progressLabel = computed(() => {
  if (!paginatedTransactions.value.length) return '0/0'
  return `${currentIndex.value + 1}/${paginatedTransactions.value.length}`
})

const displayFields = computed(() => [
  { key: 'date', label: 'Date', type: 'date', value: formattedDate(currentTransaction.value) },
  {
    key: 'category',
    label: 'Category',
    type: 'input',
    value: currentTransaction.value?.category || 'Uncategorized',
    shortcutIndex: '1',
  },
  {
    key: 'tag',
    label: 'Tag',
    type: 'input',
    formatter: (tx) => formatTagDisplay(tx),
    value: formatTagDisplay(currentTransaction.value),
    shortcutIndex: '2',
  },
  {
    key: 'merchant_name',
    label: 'Merchant',
    type: 'input',
    value: currentTransaction.value?.merchant_name || 'Unknown merchant',
    shortcutIndex: '3',
  },
  {
    key: 'description',
    label: 'Description',
    type: 'input',
    value: currentTransaction.value?.description || '',
    shortcutIndex: '4',
  },
  {
    key: 'amount',
    label: 'Amount',
    type: 'input',
    inputType: 'number',
    formatter: (tx) => formatAmount(tx.amount),
    value: currentTransaction.value?.amount ?? 0,
    shortcutIndex: '5',
  },
])

const isEditing = computed(() => {
  if (!currentTransaction.value) return false
  const txId = String(currentTransaction.value.transaction_id || '')
  return editingTransactionId.value === txId
})

const categoryFuse = computed(
  () =>
    new Fuse(
      categoryOptions.value.map((value) => ({ value })),
      {
        keys: ['value'],
        threshold: 0.3,
        ignoreLocation: true,
      },
    ),
)

const tagFuse = computed(
  () =>
    new Fuse(
      tagOptions.value.map((value) => ({ value })),
      {
        keys: ['value'],
        threshold: 0.3,
        ignoreLocation: true,
      },
    ),
)

const categorySuggestions = computed(() => {
  if (!categoryOptions.value.length) return []
  const query = (editBuffer.value.category || '').trim()
  if (!query) {
    return categoryOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  const seen = new Set()
  const matches = categoryFuse.value.search(query)
  const suggestions = []
  matches.forEach((match) => {
    if (!seen.has(match.item.value)) {
      suggestions.push(match.item.value)
      seen.add(match.item.value)
    }
  })
  if (!suggestions.length) {
    return categoryOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  return suggestions.slice(0, CATEGORY_SUGGESTION_LIMIT)
})

const tagSuggestions = computed(() => {
  if (!tagOptions.value.length) return []
  const query = (editBuffer.value.tag || '').trim()
  if (!query) {
    return tagOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  const seen = new Set()
  const matches = tagFuse.value.search(query)
  const suggestions = []
  matches.forEach((match) => {
    if (!seen.has(match.item.value)) {
      suggestions.push(match.item.value)
      seen.add(match.item.value)
    }
  })
  if (!suggestions.length) {
    return tagOptions.value.slice(0, CATEGORY_SUGGESTION_LIMIT)
  }
  return suggestions.slice(0, CATEGORY_SUGGESTION_LIMIT)
})

/**
 * Normalize tag names for local display updates.
 *
 * @param {string} value - Raw tag input.
 * @returns {string} Normalized tag label.
 */
function normalizeTagInput(value) {
  const trimmed = String(value || '').trim()
  if (!trimmed) return ''
  return trimmed.startsWith('#') ? trimmed : `#${trimmed}`
}

/**
 * Flatten category groups into unique suggestion labels.
 *
 * @param {Array<Object>} groups - Raw category groups returned by the API.
 * @returns {string[]} Sorted suggestion labels.
 */
function buildCategoryOptions(groups = []) {
  const options = []
  groups.forEach((group) => {
    const parentName = group.label || group.name
    if (parentName) {
      options.push(parentName)
    }
    ;(group.children || []).forEach((child) => {
      const childName = child.label || child.name
      if (!childName) return
      options.push(childName)
      if (parentName) {
        options.push(`${parentName}: ${childName}`)
      }
    })
  })
  const unique = Array.from(new Set(options.filter(Boolean)))
  return unique.sort((a, b) => a.localeCompare(b))
}

/**
 * Normalize tag suggestions for the review modal.
 *
 * @param {string[]} tags - Raw tag values.
 * @returns {string[]} Sorted unique tag labels.
 */
function buildTagOptions(tags = []) {
  const unique = Array.from(new Set(tags.filter(Boolean)))
  return unique.sort((a, b) => a.localeCompare(b))
}

/**
 * Fetch category groups and populate autocomplete options.
 */
async function loadCategoryOptions() {
  try {
    const response = await fetchCategoryTree()
    if (response?.status === 'success') {
      categoryOptions.value = buildCategoryOptions(response.data || [])
      return
    }
    categoryOptions.value = []
  } catch (error) {
    console.error('Failed to load category options', error)
    categoryOptions.value = []
  }
}

/**
 * Fetch tag suggestions and populate autocomplete options.
 */
async function loadTagOptions() {
  try {
    const userId = currentTransaction.value?.user_id || ''
    const tags = await fetchTagSuggestions('', CATEGORY_SUGGESTION_LIMIT * 3, userId)
    tagOptions.value = buildTagOptions(tags || [])
  } catch (error) {
    console.error('Failed to load tag options', error)
    tagOptions.value = []
  }
}

/**
 * Safely resolve a transaction date from the available fields.
 *
 * @param {Record<string, unknown>} tx - Transaction to inspect.
 * @returns {string} ISO-like date string or empty when unavailable.
 */
function resolveTransactionDate(tx) {
  if (!tx) return ''
  return tx.date || tx.transaction_date || ''
}

/**
 * Resolve the primary tag to display or edit.
 *
 * @param {Record<string, unknown>} tx - Transaction to inspect.
 * @returns {string} First non-default tag or an empty string.
 */
function resolveTransactionTag(tx) {
  if (!tx || !Array.isArray(tx.tags)) return ''
  const filtered = tx.tags.filter((tag) => tag && tag !== '#untagged')
  return filtered.length ? String(filtered[0]) : ''
}

/**
 * Format the transaction tag for display.
 *
 * @param {Record<string, unknown>} tx - Transaction to inspect.
 * @returns {string} Tag label for the UI.
 */
function formatTagDisplay(tx) {
  const resolved = resolveTransactionTag(tx)
  return resolved || '#untagged'
}

/**
 * Build an edit buffer seeded with the active transaction's current values.
 *
 * @param {Record<string, unknown>} tx - Transaction to convert.
 * @returns {Object} Prefilled edit buffer.
 */
function buildEditBuffer(tx) {
  if (!tx) return {}
  return {
    date: resolveTransactionDate(tx),
    amount: tx.amount,
    description: tx.description || '',
    category: tx.category || '',
    merchant_name: tx.merchant_name || '',
    tag: resolveTransactionTag(tx),
  }
}

/**
 * Build an edit buffer from the current transaction using editable fields.
 */
function populateEditBuffer() {
  if (!currentTransaction.value) return
  editBuffer.value = buildEditBuffer(currentTransaction.value)
}

/**
 * Store or clear an editable field input reference by key.
 *
 * @param {string} key - Edit buffer key.
 * @param {HTMLInputElement | null} element - Input element instance.
 */
function setEditInputRef(key, element) {
  if (!key) return
  if (element) {
    editInputRefs.value[key] = element
    return
  }
  delete editInputRefs.value[key]
}

/**
 * Focus an editable field by key if it is currently rendered.
 *
 * @param {string} key - Edit buffer key.
 */
function focusEditField(key) {
  const element = editInputRefs.value[key]
  if (!element) return
  element.focus()
  element.select?.()
}

/**
 * Focus one of the keyboard shortcut edit fields by index.
 *
 * @param {number} index - Zero-based index in shortcut fields.
 */
function focusShortcutField(index) {
  if (index < 0 || index >= EDIT_SHORTCUT_FIELDS.length) return
  focusEditField(EDIT_SHORTCUT_FIELDS[index])
}

/**
 * Cycle focus across the shortcut edit fields.
 *
 * @param {1 | -1} direction - Forward or backward tab direction.
 */
function cycleShortcutField(direction = 1) {
  const activeElement = document.activeElement
  const activeIndex = EDIT_SHORTCUT_FIELDS.findIndex(
    (key) => editInputRefs.value[key] === activeElement,
  )
  const fallbackIndex = direction === -1 ? EDIT_SHORTCUT_FIELDS.length - 1 : 0
  const nextIndex =
    activeIndex === -1
      ? fallbackIndex
      : (activeIndex + direction + EDIT_SHORTCUT_FIELDS.length) % EDIT_SHORTCUT_FIELDS.length
  focusShortcutField(nextIndex)
}

/**
 * Start editing the current transaction and seed the edit buffer.
 */
function beginEdit() {
  if (!currentTransaction.value) return
  populateEditBuffer()
  editingTransactionId.value = String(currentTransaction.value.transaction_id || '')
  nextTick(() => {
    focusShortcutField(0)
  })
}

/**
 * Cancel edit mode for the active transaction without advancing.
 */
function cancelEdit() {
  editingTransactionId.value = ''
  editBuffer.value = {}
}

/**
 * Reset edit state and advance to the next transaction in the batch.
 */
function advanceToNext() {
  cancelEdit()
  if (currentIndex.value < paginatedTransactions.value.length - 1) {
    currentIndex.value += 1
  } else {
    batchComplete.value = true
  }
}

/**
 * Toggle editing mode for the active transaction or cancel edits.
 */
function handleEditToggle() {
  if (isEditing.value) {
    cancelEdit()
    return
  }
  beginEdit()
}

/**
 * Validate and persist edits, then optionally save a rule for future matches.
 */
async function saveEdits() {
  if (!currentTransaction.value) return
  const payload = { transaction_id: currentTransaction.value.transaction_id }
  const editableKeys = ['date', 'amount', 'description', 'category', 'merchant_name', 'tag']
  editableKeys.forEach((key) => {
    const currentValue =
      key === 'tag'
        ? resolveTransactionTag(currentTransaction.value)
        : currentTransaction.value[key]
    if (editBuffer.value[key] !== currentValue) {
      payload[key] = editBuffer.value[key]
    }
  })

  if (Object.keys(payload).length === 1) {
    toast.info('No changes to save')
    return
  }

  if (payload.date && Number.isNaN(Date.parse(payload.date))) {
    toast.error('Invalid date')
    return
  }

  if (payload.amount != null && Number.isNaN(Number(payload.amount))) {
    toast.error('Invalid amount')
    return
  }

  try {
    await updateTransaction(payload)
    Object.assign(currentTransaction.value, payload)
    if ('tag' in payload) {
      const normalized = normalizeTagInput(payload.tag)
      currentTransaction.value.tags = [normalized || '#untagged']
    }
    toast.success('Transaction updated')
    await maybeSaveRule(payload)
  } catch (error) {
    console.error('Failed to update transaction', error)
    toast.error('Failed to update transaction')
  } finally {
    advanceToNext()
  }
}

/**
 * Prompt to save a transaction rule mirroring UpdateTransactionsTable's pattern.
 *
 * @param {Record<string, unknown>} payload - Fields that were changed.
 */
async function maybeSaveRule(payload) {
  const changedField = ['category', 'merchant_name', 'merchant_type'].find((key) => key in payload)
  if (!changedField) return
  const newValue = payload[changedField]
  const shouldCreateRule = await requestRulePrompt({
    field: changedField,
    value: newValue,
    description: currentTransaction.value.description,
    accountLabel: currentTransaction.value.account_name,
    institutionLabel: currentTransaction.value.institution_name,
  })
  if (!shouldCreateRule) return
  try {
    await createTransactionRule({
      user_id: currentTransaction.value.user_id || '',
      field: changedField,
      value: newValue,
      description: currentTransaction.value.description,
      account_id: currentTransaction.value.account_id,
    })
    toast.success('Rule saved')
  } catch (error) {
    console.error('Failed to save rule', error)
    toast.error('Failed to save rule')
  }
}

/**
 * Prompt for transaction rule creation using an explicit yes/no modal choice.
 *
 * @param {Record<string, string>} prompt - Prompt details rendered to the user.
 * @returns {Promise<boolean>} True when the user opts into saving a rule.
 */
function requestRulePrompt(prompt) {
  return new Promise((resolve) => {
    pendingRulePromptResolver = resolve
    rulePrompt.value = {
      visible: true,
      field: prompt.field,
      value: prompt.value,
      description: prompt.description,
      accountLabel: prompt.accountLabel || 'this account',
      institutionLabel: prompt.institutionLabel || 'this institution',
    }
  })
}

/**
 * Resolve and close the transaction rule prompt.
 *
 * @param {boolean} shouldCreateRule - User decision for rule creation.
 */
function resolveRulePrompt(shouldCreateRule) {
  const resolver = pendingRulePromptResolver
  pendingRulePromptResolver = null
  rulePrompt.value = {
    visible: false,
    field: '',
    value: '',
    description: '',
    accountLabel: 'this account',
    institutionLabel: 'this institution',
  }
  if (resolver) {
    resolver(shouldCreateRule)
  }
}

/**
 * Approve the transaction (no change) or save edits when editing.
 */
function handleApprove() {
  if (isEditing.value) {
    saveEdits()
    return
  }
  advanceToNext()
}

/**
 * Format the transaction date safely.
 *
 * @param {Record<string, unknown>} tx - Transaction to format.
 * @returns {string} Date label.
 */
function formattedDate(tx) {
  if (!tx) return ''
  const raw = tx.date || tx.transaction_date
  if (!raw) return 'Unknown date'
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return raw
  return date.toLocaleDateString()
}

/**
 * Start the next batch of transactions by loading the next page.
 */
async function startNextBatch() {
  if (!hasNextBatch.value) return
  batchComplete.value = false
  currentIndex.value = 0
  editingTransactionId.value = ''
  setPage(currentPage.value + 1)
  await fetchBatch(currentPage.value, { force: true })
}

/**
 * Reset modal state on close.
 */
function emitClose() {
  cancelEdit()
  batchComplete.value = false
  currentIndex.value = 0
  emit('close')
}

/**
 * Respond to keyboard arrows for edit (left) and approve/save (right).
 *
 * @param {KeyboardEvent} event - Keydown event.
 */
function handleKeydown(event) {
  if (!props.show || batchComplete.value) return
  const target = event.target
  const isEditableTarget =
    target &&
    target instanceof HTMLElement &&
    (target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.isContentEditable)

  if (isEditing.value && event.key === 'Escape') {
    event.preventDefault()
    cancelEdit()
    return
  }

  if (isEditing.value && event.key === 'Enter') {
    event.preventDefault()
    handleApprove()
    return
  }

  if (isEditing.value && event.key === 'Tab') {
    event.preventDefault()
    cycleShortcutField(event.shiftKey ? -1 : 1)
    return
  }

  if (isEditing.value && /^[1-5]$/.test(event.key)) {
    event.preventDefault()
    focusShortcutField(Number(event.key) - 1)
    return
  }

  if (isEditableTarget) return

  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    if (!isEditing.value) {
      beginEdit()
    }
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    handleApprove()
  }
}

watch(
  () => props.show,
  (visible) => {
    if (visible) {
      currentIndex.value = 0
      batchComplete.value = false
      editingTransactionId.value = ''
      fetchBatch(1, { force: true })
    }
  },
)

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadCategoryOptions()
  loadTagOptions()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
@import '../../assets/css/main.css';

.review-modal-shell {
  box-shadow: 0 30px 80px color-mix(in srgb, var(--color-accent-cyan) 18%, transparent);
}

.review-shortcuts {
  letter-spacing: 0.12em;
}

.review-field {
  border: 1px solid color-mix(in srgb, var(--divider) 70%, transparent);
  border-radius: 0.85rem;
  background: color-mix(in srgb, var(--color-bg-dark) 86%, transparent);
  padding: 0.7rem 0.8rem;
}

.review-field-value {
  min-height: 1.7rem;
  display: flex;
  align-items: center;
}

.review-input {
  min-height: 2.2rem;
  border-color: color-mix(in srgb, var(--color-accent-cyan) 25%, var(--divider));
  background: color-mix(in srgb, var(--color-bg-sec) 45%, var(--color-bg-dark));
}

.review-input:focus {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--color-accent-cyan) 50%, transparent);
}

.review-actions {
  border-top: 1px dashed color-mix(in srgb, var(--divider) 75%, transparent);
  padding-top: 1rem;
}

.review-btn-primary,
.review-btn-secondary {
  min-width: 9.25rem;
  justify-content: center;
  border-radius: 0.7rem;
}

.review-btn-primary {
  background: linear-gradient(
    135deg,
    var(--color-accent-cyan) 0%,
    color-mix(in srgb, var(--color-accent-purple) 65%, var(--color-accent-cyan)) 100%
  );
  border-color: color-mix(in srgb, var(--color-accent-cyan) 72%, var(--color-accent-purple));
  color: var(--color-bg-dark);
}

.review-btn-primary:hover {
  filter: brightness(1.07);
}

.review-btn-secondary {
  border-color: color-mix(in srgb, var(--color-accent-cyan) 55%, var(--divider));
  color: var(--color-accent-cyan);
}

.review-btn-secondary:hover {
  background: color-mix(in srgb, var(--color-accent-cyan) 20%, transparent);
  color: var(--color-text-light);
}

@media (max-width: 768px) {
  .review-btn-primary,
  .review-btn-secondary {
    width: 100%;
  }
}
</style>
