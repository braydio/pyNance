<template>
  <form @submit.prevent="onSubmit" class="space-y-4" data-testid="bill-form">
    <div>
      <label for="name" class="label">Name</label>
      <input id="name" v-model="bill.name" type="text" class="input w-full" required />
    </div>
    <div>
      <label for="amount" class="label">Amount</label>
      <input
        id="amount"
        v-model.number="bill.amount"
        type="number"
        min="0"
        step="0.01"
        class="input w-full"
        required
      />
    </div>
    <div>
      <label for="dueDate" class="label">Due Date</label>
      <input id="dueDate" v-model="bill.dueDate" type="date" class="input w-full" required />
    </div>
    <div>
      <label for="frequency" class="label">Frequency</label>
      <select id="frequency" v-model="bill.frequency" class="select w-full" required>
        <option disabled value="">Select frequency</option>
        <option value="once">Once</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
        <option value="yearly">Yearly</option>
      </select>
    </div>
    <div>
      <label for="category" class="label">Category</label>
      <input id="category" v-model="bill.category" type="text" class="input w-full" required />
    </div>
    <p v-if="error" class="text-error">{{ error }}</p>
    <div class="flex justify-end space-x-2">
      <UiButton variant="outline" type="button" @click="emitCancel">Cancel</UiButton>
      <UiButton variant="primary" type="submit">Save</UiButton>
    </div>
  </form>
</template>

<script setup>
/**
 * BillForm component.
 *
 * Provides a form for creating or editing a bill with validation for
 * required fields, positive amount and valid due date.
 *
 * Emits:
 * - `saveBill` when the form is submitted with valid data
 * - `cancel` when the user cancels the form
 */
import { reactive, ref } from 'vue'
import UiButton from '@/components/ui/Button.vue'

const emit = defineEmits(['saveBill', 'cancel'])

/** Form data for the bill. */
const bill = reactive({
  name: '',
  amount: null,
  dueDate: '',
  frequency: '',
  category: '',
})

/** Error message displayed when validation fails. */
const error = ref('')

/**
 * Validate form input and emit save event when valid.
 *
 * @returns {void}
 */
function onSubmit() {
  error.value = ''
  if (!bill.name || !bill.frequency || !bill.category) {
    error.value = 'All fields are required.'
    return
  }
  if (typeof bill.amount !== 'number' || bill.amount <= 0) {
    error.value = 'Amount must be a positive number.'
    return
  }
  const date = new Date(bill.dueDate)
  if (isNaN(date.getTime())) {
    error.value = 'Due date must be a valid date.'
    return
  }
  emit('saveBill', { ...bill })
}

/**
 * Emit cancel event to parent component.
 *
 * @returns {void}
 */
function emitCancel() {
  emit('cancel')
}
</script>

<style scoped>
/* Basic styling placeholder for BillForm */
</style>
