// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'
import TransactionReviewModal from '../TransactionReviewModal.vue'

const sampleTransactions = vi.hoisted(() => [
  {
    transaction_id: 'tx-1',
    date: '2024-01-05',
    amount: 25.5,
    description: 'Neighborhood Grocery',
    category: 'Food: Grocery',
    merchant_name: 'Fresh Foods',
    account_name: 'Checking',
    institution_name: 'Bank',
  },
])

vi.mock('vue-toastification', () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn(), info: vi.fn() }),
}))

vi.mock('@/api/transactions', () => ({
  updateTransaction: vi.fn(),
  createTransactionRule: vi.fn(),
}))

vi.mock('@/api/categories', () => ({
  fetchCategoryTree: vi.fn(async () => ({
    status: 'success',
    data: [
      { id: 'food', label: 'Food', children: [{ id: 'c1', label: 'Grocery' }] },
      { id: 'bills', label: 'Bills', children: [{ id: 'c2', label: 'Utilities' }] },
    ],
  })),
}))

vi.mock('@/composables/useTransactions', () => {
  const paginatedTransactions = ref([...sampleTransactions])
  const fetchTransactions = vi.fn().mockResolvedValue()
  return {
    useTransactions: () => ({
      paginatedTransactions,
      fetchTransactions,
      currentPage: ref(1),
      totalPages: ref(1),
      totalCount: ref(sampleTransactions.length),
      isLoading: ref(false),
      setPage: vi.fn(),
    }),
  }
})

describe('TransactionReviewModal.vue', () => {
  it('surfaces fuzzy category suggestions for approximate input', async () => {
    const wrapper = mount(TransactionReviewModal, {
      props: { show: true, filters: {} },
      global: { stubs: { transition: false } },
    })
    await flushPromises()

    wrapper.vm.beginEdit()
    wrapper.vm.editBuffer.category = 'groc'
    await flushPromises()

    expect(wrapper.vm.categorySuggestions).toContain('Food: Grocery')
    expect(wrapper.vm.categorySuggestions.length).toBeGreaterThan(0)
  })
})
