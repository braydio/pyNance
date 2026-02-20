<!-- LinkedAccountsSection.vue - Displays linked accounts organized by type and institution. -->
<template>
  <Card class="p-6 space-y-6" data-testid="linked-accounts-section">
    <header class="space-y-1">
      <h2 class="text-xl font-semibold">Linked Accounts Overview</h2>
      <p class="text-sm text-muted-foreground">
        Sorted by account category and grouped by institution for quick review of key details.
      </p>
    </header>

    <div v-if="!groupedAccounts.length" class="text-sm text-muted-foreground">
      No accounts available yet. Link an account to see details below.
    </div>

    <div v-else class="space-y-8">
      <section
        v-for="typeGroup in groupedAccounts"
        :key="typeGroup.type"
        class="space-y-4"
        :data-testid="`account-type-${typeGroup.type}`"
      >
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-semibold">{{ typeGroup.label }}</h3>
          <span class="text-xs uppercase tracking-wide text-muted-foreground">
            {{ typeGroup.institutionCount }} institutions
          </span>
        </div>

        <div class="space-y-4">
          <article
            v-for="institution in typeGroup.institutions"
            :key="institution.name"
            class="rounded-lg border border-surface-200 bg-surface-50 p-4 shadow-sm dark:border-surface-700 dark:bg-surface-900"
            :data-testid="`institution-${institution.name}`"
          >
            <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <h4 class="text-base font-semibold">{{ institution.name }}</h4>
                <p class="text-xs uppercase tracking-wide text-muted-foreground">
                  {{ institution.accounts.length }} account{{
                    institution.accounts.length === 1 ? '' : 's'
                  }}
                </p>
              </div>
            </div>

            <div class="mt-4 space-y-4">
              <div
                v-for="account in institution.accounts"
                :key="account.id"
                class="rounded-md border border-surface-200 bg-white p-4 shadow-sm dark:border-surface-600 dark:bg-surface-800"
                :data-testid="`account-${account.id}`"
              >
                <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div class="space-y-1">
                    <p class="text-base font-medium">{{ account.name }}</p>
                    <p v-if="account.mask" class="text-sm text-muted-foreground">
                      Account •••• {{ account.mask }}
                    </p>
                    <p
                      v-if="account.subtype"
                      class="text-xs uppercase tracking-wide text-muted-foreground"
                    >
                      {{ account.subtype }}
                    </p>
                  </div>

                  <div class="grid grid-cols-2 gap-4 text-sm md:text-right">
                    <div>
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">APR</p>
                      <p class="font-semibold">{{ formatApr(account.apr) }}</p>
                    </div>
                    <div v-if="account.balance !== undefined">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Balance</p>
                      <p class="font-semibold">{{ formatBalance(account.balance) }}</p>
                    </div>
                    <div v-if="account.limit !== undefined">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">
                        Credit Limit
                      </p>
                      <p class="font-semibold">{{ formatBalance(account.limit) }}</p>
                    </div>
                    <div v-if="account.status">
                      <p class="text-xs uppercase tracking-wide text-muted-foreground">Status</p>
                      <p class="font-semibold">{{ account.status }}</p>
                    </div>
                  </div>
                </div>

                <details class="mt-4 space-y-3" open>
                  <summary class="cursor-pointer text-sm font-semibold">
                    Rewards & Promotions
                  </summary>

                  <ul class="space-y-2" :data-testid="`promo-list-${account.id}`">
                    <li
                      v-for="(promotion, index) in promotionEntries[account.id] || []"
                      :key="`${account.id}-${promotion.category}-${index}`"
                      class="flex items-center justify-between rounded border border-surface-200 bg-surface-50 px-3 py-2 text-sm dark:border-surface-600 dark:bg-surface-900"
                    >
                      <span class="font-medium">{{ promotion.category }}</span>
                      <span>{{ formatPercentage(promotion.rate) }} back</span>
                    </li>
                  </ul>

                  <form
                    v-if="enablePromotionEditor"
                    class="grid gap-3 rounded-md border border-dashed border-surface-300 p-3 text-sm dark:border-surface-600"
                    @submit.prevent="addPromotion(account.id)"
                    :data-testid="`promo-form-${account.id}`"
                  >
                    <p
                      class="text-xs text-muted-foreground"
                      :data-testid="`promo-draft-label-${account.id}`"
                    >
                      Local draft only. Promotions are not persisted yet.
                    </p>
                    <div class="grid gap-2 md:grid-cols-3 md:items-end">
                      <div class="space-y-1">
                        <label
                          :for="`promo-category-${account.id}`"
                          class="text-xs uppercase tracking-wide text-muted-foreground"
                          >Category</label
                        >
                        <select
                          v-model="promotionForms[account.id].category"
                          :id="`promo-category-${account.id}`"
                          class="select select-sm"
                          :data-testid="`promo-category-${account.id}`"
                        >
                          <option
                            v-for="option in promotionCategories"
                            :key="option.value"
                            :value="option.value"
                          >
                            {{ option.label }}
                          </option>
                        </select>
                      </div>

                      <div
                        v-if="promotionForms[account.id].category === 'custom'"
                        class="space-y-1"
                      >
                        <label
                          :for="`promo-custom-category-${account.id}`"
                          class="text-xs uppercase tracking-wide text-muted-foreground"
                          >Custom Category</label
                        >
                        <input
                          v-model="promotionForms[account.id].customCategory"
                          :id="`promo-custom-category-${account.id}`"
                          type="text"
                          class="input input-sm"
                          placeholder="Describe reward"
                          :data-testid="`promo-custom-category-${account.id}`"
                        />
                      </div>

                      <div class="space-y-1">
                        <label
                          :for="`promo-rate-${account.id}`"
                          class="text-xs uppercase tracking-wide text-muted-foreground"
                          >Cash Back %</label
                        >
                        <input
                          v-model="promotionForms[account.id].rate"
                          :id="`promo-rate-${account.id}`"
                          type="number"
                          step="0.01"
                          min="0"
                          class="input input-sm"
                          placeholder="0.00"
                          :data-testid="`promo-rate-${account.id}`"
                        />
                      </div>
                    </div>

                    <div class="flex justify-end">
                      <UiButton type="submit" variant="primary" size="sm">Add Promotion</UiButton>
                    </div>
                  </form>
                </details>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </Card>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import Card from '@/components/ui/Card.vue'
import UiButton from '@/components/ui/Button.vue'
import { formatAmount } from '@/utils/format'

const promotionCategories = [
  { value: 'Groceries', label: 'Groceries' },
  { value: 'Streaming Services', label: 'Streaming Services' },
  { value: 'Gas & Transit', label: 'Gas & Transit' },
  { value: 'Dining & Restaurants', label: 'Dining & Restaurants' },
  { value: 'Travel', label: 'Travel' },
  { value: 'Online Shopping', label: 'Online Shopping' },
  { value: 'Everything Else', label: 'Everything Else' },
  { value: 'custom', label: 'Custom Category' },
]

const accountTypeLabels = {
  'Credit Card': 'Credit Cards',
  'Deposit Account': 'Checking & Savings',
  Investment: 'Investments',
}

const typeSortOrder = ['Credit Card', 'Deposit Account', 'Investment']

const defaultAccounts = [
  {
    id: 'amex-blue-cash',
    name: 'American Express Blue Cash Preferred®',
    institution: 'American Express',
    type: 'Credit Card',
    subtype: 'Cash Rewards',
    mask: '1882',
    apr: 26.99,
    balance: 1250.42,
    limit: 6500,
    status: 'Active',
    promotions: [
      { category: 'Groceries', rate: 6 },
      { category: 'Streaming Services', rate: 6 },
      { category: 'Gas & Transit', rate: 3 },
      { category: 'Everything Else', rate: 1 },
    ],
  },
  {
    id: 'wells-checking',
    name: 'Everyday Checking',
    institution: 'Wells Fargo',
    type: 'Deposit Account',
    subtype: 'Checking',
    mask: '0341',
    apr: 0,
    balance: 2435.11,
    status: 'Primary',
    promotions: [],
  },
  {
    id: 'vanguard-roth',
    name: 'Roth IRA',
    institution: 'Vanguard',
    type: 'Investment',
    subtype: 'Retirement',
    mask: '5221',
    apr: 0,
    balance: 18450.55,
    status: 'Active',
    promotions: [],
  },
]

const props = defineProps({
  accounts: {
    type: Array,
    default: () => [],
  },
  useDemoFallback: {
    type: Boolean,
    default: false,
  },
  enablePromotionEditor: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['add-promotion'])

const promotionEntries = reactive({})
const promotionForms = reactive({})

const resolvedAccounts = computed(() => {
  if (props.accounts?.length) {
    return [...props.accounts].sort((a, b) => {
      const aIndex = typeSortOrder.indexOf(a.type)
      const bIndex = typeSortOrder.indexOf(b.type)

      if (aIndex !== -1 && bIndex !== -1 && aIndex !== bIndex) {
        return aIndex - bIndex
      }
      if (aIndex !== -1 && bIndex === -1) return -1
      if (aIndex === -1 && bIndex !== -1) return 1
      if (aIndex === -1 && bIndex === -1 && a.type !== b.type) {
        return a.type.localeCompare(b.type)
      }
      return a.name.localeCompare(b.name)
    })
  }

  if (props.useDemoFallback) {
    return [...defaultAccounts]
  }

  return []
})

const groupedAccounts = computed(() => {
  const byType = new Map()

  resolvedAccounts.value.forEach((account) => {
    if (!byType.has(account.type)) {
      byType.set(account.type, new Map())
    }
    const institutionMap = byType.get(account.type)
    if (!institutionMap.has(account.institution)) {
      institutionMap.set(account.institution, [])
    }
    institutionMap.get(account.institution).push(account)
  })

  const orderedTypes = [...byType.keys()].sort((a, b) => {
    const aIndex = typeSortOrder.indexOf(a)
    const bIndex = typeSortOrder.indexOf(b)
    if (aIndex !== -1 && bIndex !== -1) {
      return aIndex - bIndex
    }
    if (aIndex !== -1) return -1
    if (bIndex !== -1) return 1
    return a.localeCompare(b)
  })

  return orderedTypes.map((type) => {
    const institutions = byType.get(type)
    const sortedInstitutions = [...institutions.entries()]
      .map(([name, accounts]) => ({
        name,
        accounts: [...accounts].sort((a, b) => a.name.localeCompare(b.name)),
      }))
      .sort((a, b) => a.name.localeCompare(b.name))

    return {
      type,
      label: accountTypeLabels[type] || type,
      institutions: sortedInstitutions,
      institutionCount: sortedInstitutions.length,
    }
  })
})

function ensurePromotionState(accounts) {
  const currentIds = new Set()

  accounts.forEach((account) => {
    currentIds.add(account.id)
    if (!promotionEntries[account.id]) {
      promotionEntries[account.id] = account.promotions ? [...account.promotions] : []
    }
    if (!promotionForms[account.id]) {
      promotionForms[account.id] = {
        category: 'Groceries',
        customCategory: '',
        rate: '',
      }
    }
  })

  Object.keys(promotionEntries).forEach((key) => {
    if (!currentIds.has(key)) {
      delete promotionEntries[key]
    }
  })
  Object.keys(promotionForms).forEach((key) => {
    if (!currentIds.has(key)) {
      delete promotionForms[key]
    }
  })
}

watch(
  resolvedAccounts,
  (accounts) => {
    ensurePromotionState(accounts)
  },
  { immediate: true },
)

function formatApr(apr) {
  if (apr === undefined || apr === null) return '—'
  return `${Number(apr).toFixed(2)}%`
}

function formatBalance(amount) {
  if (amount === undefined || amount === null) return '—'
  return formatAmount(amount)
}

function formatPercentage(value) {
  if (value === undefined || value === null || value === '') return '0%'
  const numeric = Number(value)
  if (Number.isNaN(numeric)) {
    return `${value}%`
  }
  return `${numeric % 1 === 0 ? numeric.toFixed(0) : numeric.toFixed(2)}%`
}

function resetPromotionForm(accountId) {
  promotionForms[accountId] = {
    category: 'Groceries',
    customCategory: '',
    rate: '',
  }
}

function addPromotion(accountId) {
  const form = promotionForms[accountId]
  if (!form) return

  const category = form.category === 'custom' ? form.customCategory.trim() : form.category
  if (!category) return

  const numericRate = Number(form.rate)
  if (Number.isNaN(numericRate) || numericRate < 0) {
    return
  }

  if (!promotionEntries[accountId]) {
    promotionEntries[accountId] = []
  }

  promotionEntries[accountId].push({
    category,
    rate: numericRate,
  })

  emit('add-promotion', {
    accountId,
    category,
    rate: numericRate,
  })

  resetPromotionForm(accountId)
}
</script>
