<template>
  <BasePageLayout>
    <PageHeader :icon="Calendar">
      <template #title>Planning</template>
      <template #subtitle>Manage bills, allocations, and scenario balances. </template>
      <template #actions>
        <UiButton variant="primary" @click="startCreating">Create bill</UiButton>
      </template>
    </PageHeader>

    <section class="grid gap-6 xl:grid-cols-[2fr,1fr]">
      <div class="space-y-6">
        <Card class="p-6">
          <h3 class="text-2xl font-bold">Here are a handful of notes and ideas I have for this
            page</h3>

          <p1 class="text-xs font-muted">A different form available to fill in with different fields
            for each 'type' (bills, allocations, scenarios). Provided examples of a filled out plan
            where each form type is shown several
              times over. This demonstrates a complete 'Planning' example of fully utilizing every feature here.</p1>
        <div></div>
          <p1 class="text-xs font-muted">Programmatic generation of bills (forms) based on
            automatically detected activity.</p1>
        <div></div>
          <p1 class="text-xs font-muted"> An overall synopsis or 'Profile' as an aggregate of all
            completed forms and information. A profile can be generated with a description, focus
            points, upcoming things to watch, reminders, status updates, goal timelines.</p1>
        <div></div>
          <p1 class="text-xs font-muted"> Gamefied somehow maybe?</p1>
        <div></div>
          <p1 class="text-xs font-muted"> I will come back to this. I will not forget this for
            months.</p1>
        <div></div>
          <p1 class="text-xs font-muted"> - Bullet Point</p1>
          <BillList
            :bills="billsForScenario"
            :currency-code="currencyCode"
            :selected-bill-id="selectedBillId"
            @delete="handleDeleteBill"
            @edit="handleEditBill"
            @select="handleSelectBill"
          >
            <template #actions>
              <UiButton variant="primary" @click="startCreating">Add bill</UiButton>
            </template>
          </BillList>
        </Card>

        <Card class="p-6 space-y-4">
          <header class="flex items-center justify-between">
            <h3 class="text-lg font-semibold">{{ formHeading }}</h3>
            <UiButton v-if="formVisible" variant="outline" @click="resetForm">Reset</UiButton>
          </header>
          <BillForm
            :bill="formBill"
            :currency-code="currencyCode"
            :mode="formMode"
            :visible="formVisible"
            @cancel="handleCancelBill"
            @save="handleSaveBill"
            @update:bill="handleDraftUpdate"
          />
        </Card>
      </div>

      <div class="space-y-6">
        <PlanningSummary
          :scenario-id="activeScenario?.id"
          :currency-code="currencyCode"
          @refresh="refreshSummary"
        />
        <Card class="p-6">
          <Allocator
            v-model="allocationModel"
            :available-cents="activeScenario?.planningBalanceCents ?? 0"
            :categories="allocationCategories"
            :currency-code="currencyCode"
            @change="handleAllocationChange"
          />
        </Card>
      </div>
    </section>
  </BasePageLayout>
</template>

<script setup lang="ts">
import { Calendar } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'
import UiButton from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import Allocator from '@/components/planning/Allocator.vue'
import BillForm from '@/components/planning/BillForm.vue'
import BillList from '@/components/planning/BillList.vue'
import PlanningSummary from '@/components/planning/PlanningSummary.vue'
import {
  usePlanning,
  ensureScenarioForAccount,
  persistBill,
  removeBill,
  persistScenarioAllocations,
} from '@/composables/usePlanning'
import {
  allocationsToPercentMap,
  mergePercentAllocations,
  type BillFormState,
  type BillFormSubmitPayload,
} from '@/utils/planning'
import type { Bill, Scenario } from '@/types/planning'

const route = useRoute()
const { state } = usePlanning()

const allocationModel = ref<Record<string, number>>({})
const selectedBillId = ref<string | null>(null)
const editingBill = ref<Bill | null>(null)
const draftBill = ref<BillFormState | null>(null)
const formVisible = ref(false)

const defaultAllocationTargets = ['savings:emergency', 'goal:vacation', 'invest:retirement']

const accountId = computed(() => {
  const queryValue = route.query.accountId
  return typeof queryValue === 'string' ? queryValue : ''
})

const activeScenario = computed<Scenario | undefined>(() => {
  if (accountId.value) {
    const accountScenarioId = state.activeScenarioIdByAccount[accountId.value]
    if (accountScenarioId) {
      const match = state.scenarios.find((scenario) => scenario.id === accountScenarioId)
      if (match) return match
    }
  }
  if (state.activeScenarioId) {
    return state.scenarios.find((scenario) => scenario.id === state.activeScenarioId)
  }
  return state.scenarios[0]
})

const currencyCode = computed(() => activeScenario.value?.currencyCode ?? 'USD')
const billsForScenario = computed(() => {
  const scenarioId = activeScenario.value?.id
  if (!scenarioId) return []
  return state.bills.filter((bill) => {
    if (bill.scenarioId) return bill.scenarioId === scenarioId
    return !state.activeScenarioId || scenarioId === state.activeScenarioId
  })
})

const allocationCategories = computed(() => {
  const scenario = activeScenario.value
  const scenarioTargets = scenario
    ? scenario.allocations
        .filter((allocation) => allocation.kind === 'percent')
        .map((allocation) => allocation.target)
    : []
  return Array.from(new Set([...scenarioTargets, ...defaultAllocationTargets]))
})

const formMode = computed<'create' | 'edit'>(() => (editingBill.value ? 'edit' : 'create'))
const formBill = computed(() => (formMode.value === 'edit' ? editingBill.value : null))
const formHeading = computed(() => (formMode.value === 'edit' ? 'Edit bill' : 'Create bill'))

watch(
  () => activeScenario.value?.allocations,
  (allocations) => {
    if (!allocations) {
      allocationModel.value = {}
      return
    }
    allocationModel.value = {
      ...allocationsToPercentMap(allocations),
    }
  },
  { immediate: true, deep: true },
)

watch(
  billsForScenario,
  (bills) => {
    if (!selectedBillId.value) return
    if (!bills.some((bill) => bill.id === selectedBillId.value)) {
      selectedBillId.value = null
      if (formMode.value === 'edit') {
        editingBill.value = null
        formVisible.value = false
      }
    }
  },
  { deep: true },
)

watch(accountId, () => ensureScenario(), { immediate: true })

onMounted(() => {
  ensureScenario()
})

function ensureScenario() {
  const currentAccountId = accountId.value
  return ensureScenarioForAccount(currentAccountId)
}

function startCreating() {
  editingBill.value = null
  selectedBillId.value = null
  draftBill.value = null
  formVisible.value = true
}

function handleSelectBill(bill: Bill) {
  selectedBillId.value = bill.id
  editingBill.value = { ...bill }
  draftBill.value = null
  formVisible.value = true
}

function handleEditBill(bill: Bill) {
  selectedBillId.value = bill.id
  editingBill.value = { ...bill }
  draftBill.value = null
  formVisible.value = true
}

async function handleDeleteBill(id: string) {
  if (typeof window !== 'undefined') {
    const confirmed = window.confirm('Delete this bill? This action cannot be undone.')
    if (!confirmed) return
  }

  try {
    await removeBill(id)
  } catch (error) {
    console.error('Failed to delete bill', error)
    return
  }

  if (selectedBillId.value === id) {
    selectedBillId.value = null
    editingBill.value = null
    formVisible.value = false
  }
}

function handleDraftUpdate(draft: BillFormState) {
  const scenario = activeScenario.value
  if (scenario && formMode.value === 'create') {
    draftBill.value = {
      ...draft,
      scenarioId: scenario.id,
      accountId: scenario.accountId,
    }
  } else {
    draftBill.value = draft
  }
}

async function handleSaveBill(payload: BillFormSubmitPayload) {
  const scenario = activeScenario.value ?? ensureScenario()
  if (!scenario) return

  try {
    const persisted = await persistBill({
      ...payload,
      scenarioId: payload.scenarioId ?? scenario.id,
      accountId: payload.accountId ?? draftBill.value?.accountId ?? scenario.accountId,
    })

    if (payload.id) {
      editingBill.value = null
      formVisible.value = false
      selectedBillId.value = persisted.id
    } else {
      editingBill.value = { ...persisted }
      formVisible.value = true
      selectedBillId.value = persisted.id
    }

    draftBill.value = null
  } catch (error) {
    console.error('Failed to persist bill', error)
  }
}

function handleCancelBill() {
  formVisible.value = false
  editingBill.value = null
  draftBill.value = null
}

function resetForm() {
  if (formMode.value === 'edit' && selectedBillId.value) {
    const bill = state.bills.find((existing) => existing.id === selectedBillId.value)
    editingBill.value = bill ? { ...bill } : null
  } else {
    draftBill.value = null
    editingBill.value = null
  }
}

async function handleAllocationChange({ allocations }: { allocations: Record<string, number> }) {
  const scenario = activeScenario.value ?? ensureScenario()
  if (!scenario) return

  const updatedAllocations = mergePercentAllocations(scenario.allocations, allocations, () =>
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `alloc-${Date.now()}`,
  )

  try {
    await persistScenarioAllocations(scenario.id, updatedAllocations)
  } catch (error) {
    console.error('Failed to persist allocations', error)
  }
}

function refreshSummary() {
  ensureScenario()
}
</script>
