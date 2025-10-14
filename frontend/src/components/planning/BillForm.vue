<template>
  <form
    v-if="visible"
    class="space-y-6"
    data-testid="bill-form"
    @submit.prevent="handleSubmit"
  >
    <div class="grid gap-4 sm:grid-cols-2">
      <div class="space-y-1 sm:col-span-2">
        <label for="bill-name" class="label">Bill name</label>
        <input
          id="bill-name"
          v-model="form.name"
          type="text"
          class="input w-full"
          name="name"
          autocomplete="off"
          @blur="markTouched('name')"
        />
        <p v-if="errors.name" class="text-sm text-error">{{ errors.name }}</p>
      </div>

      <div class="space-y-1 sm:col-span-2">
        <label for="bill-amount" class="label">Amount</label>
        <div class="relative">
          <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-muted">
            {{ currencySymbol }}
          </span>
          <input
            id="bill-amount"
            v-model="form.amount"
            type="text"
            inputmode="decimal"
            class="input w-full pl-8"
            name="amount"
            autocomplete="off"
            @blur="markTouched('amount')"
          />
        </div>
        <div class="flex items-center justify-between text-sm text-muted">
          <span>Formatted: {{ amountPreview }}</span>
          <span v-if="form.amount">{{ centsPreview }}</span>
        </div>
        <p v-if="errors.amount" class="text-sm text-error">{{ errors.amount }}</p>
      </div>

      <div class="space-y-1">
        <label for="bill-due-date" class="label">Due date</label>
        <input
          id="bill-due-date"
          v-model="form.dueDate"
          type="date"
          class="input w-full"
          name="dueDate"
          @blur="markTouched('dueDate')"
        />
        <p v-if="errors.dueDate" class="text-sm text-error">{{ errors.dueDate }}</p>
      </div>

      <div class="space-y-1">
        <label for="bill-frequency" class="label">Frequency</label>
        <select
          id="bill-frequency"
          v-model="form.frequency"
          class="select w-full"
          name="frequency"
          @blur="markTouched('frequency')"
        >
          <option disabled value="">Select frequency</option>
          <option v-for="option in frequencyOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <p v-if="errors.frequency" class="text-sm text-error">{{ errors.frequency }}</p>
      </div>

      <div class="space-y-1 sm:col-span-2">
        <label for="bill-category" class="label">Category</label>
        <input
          id="bill-category"
          v-model="form.category"
          type="text"
          class="input w-full"
          name="category"
          autocomplete="off"
          @blur="markTouched('category')"
        />
        <p v-if="errors.category" class="text-sm text-error">{{ errors.category }}</p>
      </div>
    </div>

    <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p class="text-sm text-muted">
        {{ helperCopy }}
      </p>
      <div class="flex gap-2 sm:justify-end">
        <UiButton variant="outline" type="button" @click="handleCancel">Cancel</UiButton>
        <UiButton :disabled="!isValid" type="submit" variant="primary">
          {{ submitLabel }}
        </UiButton>
      </div>
    </div>
  </form>
  <div v-else class="rounded border border-dashed border-muted p-6 text-center text-sm text-muted">
    Select a bill to edit or choose "Create bill" to start planning.
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import UiButton from '@/components/ui/Button.vue'
import type { Bill, BillFrequency } from '@/types/planning'
import { formatCurrency } from '@/utils/currency'
import {
  billToFormState,
  normaliseBillForm,
  parseCurrencyInput,
  type BillFormState,
  type BillFormSubmitPayload,
} from '@/utils/planning'

const frequencyOptions: Array<{ value: BillFrequency; label: string }> = [
  { value: 'once', label: 'Once' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
]

type EditableField = 'name' | 'amount' | 'dueDate' | 'frequency' | 'category'

const props = withDefaults(
  defineProps<{
    bill?: Bill | null
    currencyCode?: string
    mode?: 'create' | 'edit'
    visible?: boolean
  }>(),
  {
    currencyCode: 'USD',
    mode: 'create',
    visible: true,
  },
)

const emit = defineEmits<{
  (e: 'update:bill', draft: BillFormState): void
  (e: 'save', payload: BillFormSubmitPayload): void
  (e: 'cancel'): void
}>()

const form = reactive<BillFormState>(billToFormState(props.bill))
const errors = reactive<Record<EditableField, string>>({
  name: '',
  amount: '',
  dueDate: '',
  frequency: '',
  category: '',
})
const touched = reactive<Record<EditableField, boolean>>({
  name: false,
  amount: false,
  dueDate: false,
  frequency: false,
  category: false,
})
const isValid = computed(() => Object.values(errors).every((message) => !message))
const submitLabel = computed(() => (props.mode === 'edit' ? 'Save changes' : 'Add bill'))
const helperCopy = computed(() =>
  props.mode === 'edit'
    ? 'Update the bill details and save when you are ready.'
    : 'Fill in the form to plan an upcoming expense.',
)

const amountValue = computed(() => parseCurrencyInput(form.amount))
const amountPreview = computed(() =>
  Number.isFinite(amountValue.value) && amountValue.value > 0
    ? formatCurrency(amountValue.value, props.currencyCode)
    : formatCurrency(0, props.currencyCode),
)
const centsPreview = computed(() => {
  if (!Number.isFinite(amountValue.value) || amountValue.value <= 0) return ''
  const cents = Math.round(amountValue.value * 100)
  return `${cents.toLocaleString()}¢`
})

const currencySymbol = computed(() => formatCurrency(0, props.currencyCode).replace(/[0\d.,\s]/g, '') || '$')

let resetting = false

watch(
  () => props.bill,
  (bill) => {
    resetting = true
    Object.assign(form, billToFormState(bill))
    resetValidation()
    emitDraft()
    resetting = false
  },
  { immediate: true },
)

watch(
  form,
  () => {
    emitDraft()
    if (resetting) return
    (Object.keys(touched) as EditableField[]).forEach((field) => {
      if (touched[field]) {
        validateField(field)
      }
    })
  },
  { deep: true },
)

function emitDraft() {
  emit('update:bill', { ...form })
}

function resetValidation() {
  (Object.keys(errors) as EditableField[]).forEach((field) => {
    errors[field] = ''
    touched[field] = false
  })
}

function markTouched(field: EditableField) {
  touched[field] = true
  validateField(field)
}

function validateField(field: EditableField) {
  switch (field) {
    case 'name':
      errors.name = form.name.trim() ? '' : 'Name is required.'
      break
    case 'amount': {
      const value = parseCurrencyInput(form.amount)
      errors.amount = !Number.isFinite(value) || value <= 0 ? 'Enter a positive amount.' : ''
      break
    }
    case 'dueDate':
      errors.dueDate = form.dueDate ? '' : 'Due date is required.'
      break
    case 'frequency':
      errors.frequency = form.frequency ? '' : 'Select a frequency.'
      break
    case 'category':
      errors.category = form.category.trim() ? '' : 'Category is required.'
      break
    default:
      break
  }
}

function validateAll(): boolean {
  (Object.keys(touched) as EditableField[]).forEach((field) => {
    touched[field] = true
    validateField(field)
  })
  return isValid.value
}

function handleSubmit() {
  if (!validateAll()) return

  const payload = normaliseBillForm(form, props.bill)
  emit('save', payload)

  if (props.mode === 'create') {
    resetting = true
    Object.assign(form, billToFormState(null))
    resetValidation()
    emitDraft()
    resetting = false
  }
}

function handleCancel() {
  emit('cancel')
  resetting = true
  Object.assign(form, billToFormState(props.bill))
  resetValidation()
  emitDraft()
  resetting = false
}
</script>
