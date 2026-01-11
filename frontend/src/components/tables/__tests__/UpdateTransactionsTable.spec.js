// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UpdateTransactionsTable from '../UpdateTransactionsTable.vue'
import { updateTransaction, createTransactionRule } from '@/api/transactions'

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

vi.mock('@/api/transactions', () => ({
  updateTransaction: vi.fn(),
  createTransactionRule: vi.fn(),
  fetchCategoryTree: vi.fn(async () => ({
    status: 'success',
    data: [
      { id: 'food', label: 'Food', children: [{ id: 'c1', label: 'Grocery' }] },
      { id: 'bills', label: 'Bills', children: [{ id: 'c2', label: 'Utilities' }] },
    ],
  })),
  fetchMerchantSuggestions: vi.fn(async () => []),
}))

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

  it('sorts transactions by date descending by default', async () => {
    const transactions = [
      {
        transaction_id: 'old',
        date: '2023-01-01',
        amount: 10,
        description: 'Oldest',
        category: 'Food: Grocery',
        merchant_name: 'M1',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
      {
        transaction_id: 'new',
        date: '2024-05-01',
        amount: 20,
        description: 'Newest',
        category: 'Bills: Utilities',
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

    const displayed = wrapper.vm.displayTransactions.filter((tx) => !tx._placeholder)
    expect(displayed[0].transaction_id).toBe('new')
  })

  it('supports fuzzy filtering on selected field', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'Grocery Market',
        category: 'Food: Grocery',
        merchant_name: 'Fresh Foods',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
      {
        transaction_id: 't2',
        date: '2024-01-02',
        amount: 20,
        description: 'Online Subscription',
        category: 'Bills: Utilities',
        merchant_name: 'Streamio',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })

    wrapper.vm.selectFilterField('description')
    wrapper.vm.fieldSearch = 'market'
    wrapper.vm.addFieldFilter()
    await flushPromises()

    const displayed = wrapper.vm.displayTransactions.filter((tx) => !tx._placeholder)
    expect(displayed).toHaveLength(1)
    expect(displayed[0].transaction_id).toBe('t1')
  })

  it('surfaces fuzzy category suggestions for approximate input', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'Grocery Market',
        category: 'Food: Grocery',
        merchant_name: 'Fresh Foods',
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
        merchant_name: 'Power Co',
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

    wrapper.vm.startEdit(0, transactions[0])
    wrapper.vm.editBuffer.category = 'groc'
    await flushPromises()

    expect(wrapper.vm.categorySuggestions).toContain('Food: Grocery')
    expect(wrapper.vm.categorySuggestions.length).toBeGreaterThan(0)
  })

  it('stacks multiple field filters', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'Grocery Market',
        category: 'Food: Grocery',
        merchant_name: 'Fresh Foods',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
      {
        transaction_id: 't2',
        date: '2024-01-02',
        amount: 20,
        description: 'Grocery Market',
        category: 'Food: Grocery',
        merchant_name: 'Streamio',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })

    wrapper.vm.selectFilterField('description')
    wrapper.vm.fieldSearch = 'grocery'
    wrapper.vm.addFieldFilter()
    wrapper.vm.selectFilterField('merchant_name')
    wrapper.vm.fieldSearch = 'fresh'
    wrapper.vm.addFieldFilter()
    await flushPromises()

    const displayed = wrapper.vm.displayTransactions.filter((tx) => !tx._placeholder)
    expect(displayed).toHaveLength(1)
    expect(displayed[0].transaction_id).toBe('t1')
  })

  it('auto-enters edit mode when a promoted transaction id is provided', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        date: '2024-01-01',
        amount: 10,
        description: 'Grocery Market',
        category: 'Food: Grocery',
        merchant_name: 'Fresh Foods',
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
        merchant_name: 'Power Co',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 's',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions, autoEditTransactionId: 't2' },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })
    await flushPromises()

    expect(wrapper.vm.editingTransactionId).toBe('t2')
  })

  it('preloads edit inputs with the current transaction values', async () => {
    const transactions = [
      {
        transaction_id: 't1',
        transaction_date: '2024-02-15',
        amount: -42.5,
        description: 'Sample transaction',
        category: 'Bills',
        merchant_name: 'Utility Co',
        account_name: 'A1',
        institution_name: 'I1',
        subtype: 'checking',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })

    wrapper.vm.startEdit(0, transactions[0])
    await flushPromises()

    const editingRow = wrapper.find('tr.row-editing')
    expect(editingRow.exists()).toBe(true)

    const dateInput = editingRow.find('input[type="date"]')
    const amountInput = editingRow.find('input[type="number"]')
    const descriptionInput = editingRow.find('input[type="text"]')

    expect(dateInput.element.value).toBe('2024-02-15')
    expect(amountInput.element.value).toBe('-42.5')
    expect(descriptionInput.element.value).toBe('Sample transaction')
  })

  it('enables virtualization for large datasets', async () => {
    const transactions = Array.from({ length: 120 }, (_, index) => ({
      transaction_id: `t-${index}`,
      date: '2024-01-01',
      amount: index,
      description: `Transaction ${index}`,
      category: 'Food: Grocery',
      merchant_name: 'Vendor',
      account_name: 'A1',
      institution_name: 'I1',
      subtype: 's',
    }))

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions, pageSize: transactions.length },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })

    expect(wrapper.vm.useVirtualization).toBe(true)
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

  it('builds rule prompts from the edited transaction when rows shift', async () => {
    updateTransaction.mockResolvedValue({})
    createTransactionRule.mockResolvedValue({})
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    const transactions = [
      {
        transaction_id: 'alpha',
        date: '2024-01-01',
        amount: 10,
        description: 'Coffee Shop',
        category: 'Food: Coffee',
        merchant_name: 'Cafe',
        account_name: 'Everyday Checking',
        institution_name: 'Bank A',
        account_id: 'acct-1',
      },
      {
        transaction_id: 'beta',
        date: '2024-01-02',
        amount: 25,
        description: 'Electric Utility',
        category: 'Bills: Utilities',
        merchant_name: 'PowerGrid',
        account_name: 'Bills Checking',
        institution_name: 'Bank B',
        account_id: 'acct-2',
      },
    ]

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })
    await flushPromises()

    wrapper.vm.startEdit(1, transactions[1])
    wrapper.vm.editBuffer.category = 'Household'

    // Simulate the virtualized row changing beneath the edit state.
    await wrapper.vm.saveEdit(transactions[0])
    await flushPromises()

    expect(confirmSpy).toHaveBeenCalled()
    const promptText = confirmSpy.mock.calls[0][0]
    expect(promptText).toContain('Electric Utility')
    expect(createTransactionRule).toHaveBeenCalledWith(
      expect.objectContaining({
        description: 'Electric Utility',
        account_id: 'acct-2',
      }),
    )

    confirmSpy.mockRestore()
  })
})
