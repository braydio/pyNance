<template>
  <form
    v-if="visible"
    class="bill-form"
    data-testid="bill-form"
    @submit.prevent="handleSubmit"
  >
    <section class="form-section" aria-labelledby="bill-details-heading">
      <header class="section-header">
        <span class="section-eyebrow">{{ sectionEyebrow }}</span>
        <h4 id="bill-details-heading" class="section-title">{{ sectionTitle }}</h4>
        <p class="section-description">
          {{ helperCopy }}
        </p>
      </header>

      <div class="section-grid">
        <div class="form-field form-field--full">
          <label for="bill-name" class="field-label">Bill name</label>
          <input
            id="bill-name"
            v-model="form.name"
            type="text"
            class="form-control"
            name="name"
            autocomplete="off"
            @blur="markTouched('name')"
          />
          <p v-if="errors.name" class="error-message">{{ errors.name }}</p>
        </div>

        <div class="form-field form-field--full">
          <label for="bill-amount" class="field-label">Amount</label>
          <div class="input-with-prefix">
            <span class="currency-prefix">
              {{ currencySymbol }}
            </span>
            <input
              id="bill-amount"
              v-model="form.amount"
              type="text"
              inputmode="decimal"
              class="form-control has-prefix"
              name="amount"
              autocomplete="off"
              @blur="markTouched('amount')"
            />
          </div>
          <div class="field-meta">
            <span>Formatted: {{ amountPreview }}</span>
            <span v-if="form.amount">{{ centsPreview }}</span>
          </div>
          <p v-if="errors.amount" class="error-message">{{ errors.amount }}</p>
        </div>

        <div class="form-field">
          <label for="bill-due-date" class="field-label">Due date</label>
          <input
            id="bill-due-date"
            v-model="form.dueDate"
            type="date"
            class="form-control"
            name="dueDate"
            @blur="markTouched('dueDate')"
          />
          <p v-if="errors.dueDate" class="error-message">{{ errors.dueDate }}</p>
        </div>

        <div class="form-field">
          <label for="bill-frequency" class="field-label">Frequency</label>
          <select
            id="bill-frequency"
            v-model="form.frequency"
            class="form-control"
            name="frequency"
            @blur="markTouched('frequency')"
          >
            <option disabled value="">Select frequency</option>
            <option v-for="option in frequencyOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <p v-if="errors.frequency" class="error-message">{{ errors.frequency }}</p>
        </div>

        <div class="form-field form-field--full">
          <label for="bill-category" class="field-label">Category</label>
          <input
            id="bill-category"
            v-model="form.category"
            type="text"
            class="form-control"
            name="category"
            autocomplete="off"
            @blur="markTouched('category')"
          />
          <p v-if="errors.category" class="error-message">{{ errors.category }}</p>
        </div>
      </div>
    </section>

    <footer class="form-actions">
      <p class="action-copy">
        {{ actionCopy }}
      </p>
      <div class="button-group">
        <UiButton variant="outline" type="button" @click="handleCancel">Cancel</UiButton>
        <UiButton :disabled="!isValid" type="submit" variant="primary">
          {{ submitLabel }}
        </UiButton>
      </div>
    </footer>
  </form>
  <div v-else class="form-placeholder">
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
const sectionEyebrow = computed(() => (props.mode === 'edit' ? 'Editing bill' : 'New planned bill'))
const sectionTitle = computed(() =>
  props.mode === 'edit' ? 'Update bill details' : 'Bill details',
)
const actionCopy = computed(() =>
  props.mode === 'edit'
    ? 'Save your updates or cancel to restore the previous information.'
    : 'Add the bill to your plan when you are happy with the details.',
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

const currencySymbol = computed(
  () => formatCurrency(0, props.currencyCode).replace(/[0\d.,\s]/g, '') || '$',
)

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
    ;(Object.keys(touched) as EditableField[]).forEach((field) => {
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
  ;(Object.keys(errors) as EditableField[]).forEach((field) => {
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
  ;(Object.keys(touched) as EditableField[]).forEach((field) => {
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

<style scoped>
@reference "../../assets/css/main.css";

.bill-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  padding: 1.75rem;
  border-radius: 1rem;
  border: 1px solid var(--divider);
  background: linear-gradient(145deg, rgba(41, 57, 79, 0.82), rgba(25, 35, 48, 0.9));
  box-shadow: 0 20px 40px -28px rgba(13, 23, 42, 0.9);
  backdrop-filter: blur(6px);
}

.section-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-eyebrow {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.section-description {
  color: var(--color-text-muted);
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 38rem;
}

.section-grid {
  display: grid;
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.form-field--full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-primary);
}

.form-control {
  width: 100%;
  border-radius: 0.75rem;
  border: 1px solid var(--divider);
  background-color: var(--input-bg);
  color: var(--text-primary);
  font-size: 0.95rem;
  padding: 0.75rem 0.9rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-control:focus {
  outline: none;
  border-color: var(--color-accent-cyan);
  box-shadow: 0 0 0 3px rgba(99, 205, 207, 0.18);
}

.input-with-prefix {
  position: relative;
}

.currency-prefix {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 0.85rem;
  color: var(--color-text-muted);
  pointer-events: none;
}

.form-control.has-prefix {
  padding-left: 2.4rem;
}

.field-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.error-message {
  font-size: 0.85rem;
  color: var(--color-error);
  font-weight: 500;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.25rem 1.5rem;
  border-radius: 0.9rem;
  border: 1px solid rgba(99, 205, 207, 0.18);
  background: rgba(113, 156, 214, 0.12);
}

.action-copy {
  font-size: 0.9rem;
  color: var(--text-primary);
  line-height: 1.6;
}

.button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-start;
}

.form-placeholder {
  border-radius: 1rem;
  border: 1px dashed var(--divider);
  padding: 2rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  background: rgba(41, 57, 79, 0.4);
}

@media (min-width: 640px) {
  .section-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-actions {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }

  .button-group {
    justify-content: flex-end;
  }
}
</style>
