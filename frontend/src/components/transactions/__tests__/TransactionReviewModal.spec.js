// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import TransactionReviewModal from '../TransactionReviewModal.vue'
import { createTransactionRule, updateTransaction } from '@/api/transactions'

const sampleTransaction = vi.hoisted(() => ({
  transaction_id: 'tx-1',
  transaction_date: '2024-03-10',
  amount: 125.75,
  description: 'Cafe brunch',
  category: 'Dining',
  merchant_name: 'Weekend Cafe',
  account_name: 'Checking',
  institution_name: 'Bank',
}))

vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), info: vi.fn() }),
}))

vi.mock('@/composables/useTransactions', () => {
  const paginatedTransactions = ref([sampleTransaction])
  const fetchTransactions = vi.fn(() => Promise.resolve())
  const setPage = vi.fn()
  return {
    useTransactions: vi.fn(() => ({
      paginatedTransactions,
      fetchTransactions,
      currentPage: ref(1),
      totalPages: ref(1),
      totalCount: ref(1),
      isLoading: ref(false),
      setPage,
    })),
  }
})

vi.mock('@/api/transactions', () => ({
  updateTransaction: vi.fn(() => Promise.resolve()),
  createTransactionRule: vi.fn(() => Promise.resolve()),
  fetchTagSuggestions: vi.fn(() => Promise.resolve([])),
}))

vi.mock('@/api/categories', () => ({
  fetchCategoryTree: vi.fn(() => Promise.resolve({ status: 'success', data: [] })),
}))

function findInputByLabel(wrapper, labelText) {
  const labelWrapper = wrapper.findAll('label').find((node) => node.text() === labelText)
  if (!labelWrapper) return null
  return labelWrapper.element.parentElement.querySelector('input')
}

describe('TransactionReviewModal.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('seeds edit inputs with the active transaction values when entering edit mode', async () => {
    const wrapper = mount(TransactionReviewModal, {
      props: { show: true, filters: {} },
    })

    await flushPromises()

    const editButton = wrapper.get('.btn-outline')
    await editButton.trigger('click')
    await flushPromises()

    const dateInput = findInputByLabel(wrapper, 'Date')
    const amountInput = findInputByLabel(wrapper, 'Amount')
    const descriptionInput = findInputByLabel(wrapper, 'Description')

    expect(dateInput?.value).toBe('2024-03-10')
    expect(amountInput?.value).toBe('125.75')
    expect(descriptionInput?.value).toBe('Cafe brunch')
  })

  it('supports keyboard-first editing shortcuts and save flow', async () => {
    const wrapper = mount(TransactionReviewModal, {
      props: { show: true, filters: {} },
      attachTo: document.body,
    })

    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }))
    await flushPromises()

    const categoryInput = findInputByLabel(wrapper, 'Category')
    const descriptionInput = findInputByLabel(wrapper, 'Description')
    expect(document.activeElement).toBe(categoryInput)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: '4', bubbles: true }))
    await flushPromises()
    expect(document.activeElement).toBe(descriptionInput)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))
    await flushPromises()
    const amountInput = findInputByLabel(wrapper, 'Amount')
    expect(document.activeElement).toBe(amountInput)

    await wrapper.get('input[type="number"]').setValue('200')
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    await flushPromises()

    expect(updateTransaction).toHaveBeenCalled()
    const lastUpdatePayload = updateTransaction.mock.calls.at(-1)?.[0] || {}
    expect(lastUpdatePayload.transaction_id).toBe('tx-1')
    expect(lastUpdatePayload.amount).toBe(200)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowLeft', bubbles: true }))
    await flushPromises()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await flushPromises()

    expect(findInputByLabel(wrapper, 'Category')).toBeNull()
  })

  it('allows skipping rule creation when declining the save rule prompt', async () => {
    const wrapper = mount(TransactionReviewModal, {
      props: { show: true, filters: {} },
      attachTo: document.body,
    })

    await flushPromises()

    await wrapper.get('.btn-outline').trigger('click')
    await flushPromises()

    const categoryInput = findInputByLabel(wrapper, 'Category')
    expect(categoryInput).not.toBeNull()

    categoryInput.value = 'Dining Out'
    categoryInput.dispatchEvent(new Event('input'))
    await flushPromises()

    await wrapper.get('.review-btn-primary').trigger('click')
    await flushPromises()

    expect(wrapper.vm.rulePrompt.visible).toBe(true)
    wrapper.vm.resolveRulePrompt(false)
    await flushPromises()

    expect(createTransactionRule).not.toHaveBeenCalled()
  })
})
