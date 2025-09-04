// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UpdateTransactionsTable from '../UpdateTransactionsTable.vue'
import { updateTransaction } from '@/api/transactions'

// Mock API dependencies
vi.mock('axios', () => {
  const get = vi.fn().mockResolvedValue({
    data: {
      status: 'success',
      data: [
        { name: 'Food', children: [{ id: 'c1', name: 'Grocery' }] },
        { name: 'Bills', children: [{ id: 'c2', name: 'Utilities' }] },
      ],
    },
  })
  return { default: { get }, get }
})

vi.mock('vue-toastification', () => ({
  useToast: () => ({ info: vi.fn(), error: vi.fn(), success: vi.fn() }),
}))

vi.mock('@/api/transactions', () => ({ updateTransaction: vi.fn() }))
import { updateTransaction } from '@/api/transactions'

describe('UpdateTransactionsTable.vue', () => {
  it('filters transactions by primary category', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'Grocery',
        category: 'Food: Grocery',
        primary_category: 'Food',
        merchant_name: 'M1',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
      {
        transaction_id: 't2',
        date: '2024-01-02',
        amount: 20,
        description: 'Utility',
        category: 'Bills: Utilities',
        primary_category: 'Bills',
        merchant_name: 'M2',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })
    await flushPromises()

    // directly set primary category and verify filtering
    wrapper.vm.selectedPrimaryCategory = 'Food'
    await flushPromises()

    const displayed = wrapper.vm.displayTransactions.filter((tx) => !tx._placeholder)
    expect(displayed).toHaveLength(1)
    expect(displayed[0].transaction_id).toBe('t1')
})

  it('prompts for internal counterpart selection', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'A',
        merchant_name: 'M1',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
      {
        transaction_id: 't2',
        date: '2024-01-02',
        amount: -10,
        description: 'B',
        merchant_name: 'M2',
        account_name: 'A2',
        institution_name: 'I2',
        subtype: 's',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })

    await wrapper.vm.toggleInternal(transactions[0])
    expect(wrapper.vm.showInternalModal).toBe(true)
    expect(wrapper.vm.internalCandidates).toHaveLength(1)
    expect(wrapper.vm.internalCandidates[0].id).toBe('t2')

    wrapper.vm.selectedCounterpart = ['t2']
    await wrapper.vm.confirmInternal()
    expect(updateTransaction).toHaveBeenCalledWith({
      transaction_id: 't1',
      is_internal: true,
      counterpart_transaction_id: 't2',
      flag_counterpart: true,
    })
    expect(transactions[0].is_internal).toBe(true)
    expect(transactions[1].is_internal).toBe(true)
  })
})
