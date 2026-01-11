// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import TransactionReviewModal from '../TransactionReviewModal.vue'

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
  updateTransaction: vi.fn(),
  createTransactionRule: vi.fn(),
  fetchTagSuggestions: vi.fn(() => Promise.resolve([])),
}))

function findInputByLabel(wrapper, labelText) {
  const labelWrapper = wrapper.findAll('label').find((node) => node.text() === labelText)
  if (!labelWrapper) return null
  return labelWrapper.element.parentElement.querySelector('input')
}

describe('TransactionReviewModal.vue', () => {
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
})
