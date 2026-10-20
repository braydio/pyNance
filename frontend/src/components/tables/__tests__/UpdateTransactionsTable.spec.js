// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
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
  beforeEach(() => {
    vi.clearAllMocks()
  })

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
    const savePromise = wrapper.vm.saveEdit(transactions[0])
    await flushPromises()

    expect(wrapper.vm.rulePrompt.visible).toBe(true)
    expect(wrapper.vm.rulePrompt.description).toBe('Electric Utility')

    wrapper.vm.resolveRulePrompt(true)
    await savePromise
    await flushPromises()

    expect(createTransactionRule).toHaveBeenCalledWith(
      expect.objectContaining({
        description: 'Electric Utility',
        account_id: 'acct-2',
      }),
    )
  })

  it('allows explicitly skipping rule creation from the save prompt', async () => {
    updateTransaction.mockResolvedValue({})
    createTransactionRule.mockResolvedValue({})

    const transaction = {
      transaction_id: 'alpha',
      date: '2024-01-01',
      amount: 10,
      description: 'Coffee Shop',
      category: 'Food: Coffee',
      merchant_name: 'Cafe',
      account_name: 'Everyday Checking',
      institution_name: 'Bank A',
      account_id: 'acct-1',
    }

    const wrapper = mount(UpdateTransactionsTable, {
      props: { transactions: [transaction] },
      global: { stubs: ['Modal', 'FuzzyDropdown'] },
    })
    await flushPromises()

    wrapper.vm.startEdit(0, transaction)
    wrapper.vm.editBuffer.category = 'Household'

    const savePromise = wrapper.vm.saveEdit(transaction)
    await flushPromises()

    expect(wrapper.vm.rulePrompt.visible).toBe(true)
    wrapper.vm.resolveRulePrompt(false)
    await savePromise
    await flushPromises()

    expect(createTransactionRule).not.toHaveBeenCalled()
  })

  describe('grid accessibility and column priority', () => {
    const rows = [
      {
        transaction_id: 'a',
        date: '2024-01-01',
        amount: 10,
        description:
          'A very long description that should truncate in the cell but remain available',
        category: 'Food',
        merchant_name: 'Merchant A',
        account_name: 'Checking',
        institution_name: 'Bank',
        subtype: 'checking',
        running_balance: 100,
      },
      {
        transaction_id: 'b',
        date: '2024-02-01',
        amount: -20,
        description: 'B',
        category: 'Bills',
        merchant_name: 'Merchant B',
        account_name: 'Savings',
        institution_name: 'Bank',
        subtype: 'savings',
        running_balance: 80,
      },
    ]
    const mountTable = () =>
      mount(UpdateTransactionsTable, {
        props: { transactions: rows },
        global: { stubs: ['Modal', 'FuzzyDropdown'] },
        attachTo: document.body,
      })

    it('sorts from a real button inside each header and reports aria-sort', async () => {
      const wrapper = mountTable()
      const dateHeader = wrapper.get('th.col-date')
      expect(dateHeader.attributes('aria-sort')).toBe('descending')
      expect(wrapper.get('th.col-amount').attributes('aria-sort')).toBe('none')

      const button = wrapper.get('[data-testid="sort-amount"]')
      expect(button.element.tagName).toBe('BUTTON')
      expect(button.attributes('type')).toBe('button')
      await button.trigger('click')
      expect(wrapper.get('th.col-amount').attributes('aria-sort')).toBe('descending')
      await button.trigger('click')
      expect(wrapper.get('th.col-amount').attributes('aria-sort')).toBe('ascending')
      expect(wrapper.get('th.col-date').attributes('aria-sort')).toBe('none')
      expect(wrapper.get('th.col-actions').attributes('aria-sort')).toBeUndefined()
      wrapper.unmount()
    })

    it('shows the priority columns by default and lets secondary columns be chosen', async () => {
      const wrapper = mountTable()
      const headers = () =>
        wrapper.findAll('thead th').map((th) => th.text().replace(/\s*[▲▼]/, ''))
      expect(headers()).toEqual(
        expect.arrayContaining(['Date', 'Amount', 'Description', 'Category', 'Account', 'Actions']),
      )
      expect(headers().join(' ')).not.toContain('Institution')
      expect(headers().join(' ')).not.toContain('Running balance')

      await wrapper.get('[data-testid="column-toggle-institution"]').setValue(true)
      await wrapper.get('[data-testid="column-toggle-running"]').setValue(true)
      expect(headers().join(' ')).toContain('Institution')
      expect(headers().join(' ')).toContain('Running balance')
      expect(wrapper.find('td.col-institution').exists()).toBe(true)

      await wrapper.get('[data-testid="column-toggle-institution"]').setValue(false)
      expect(wrapper.find('td.col-institution').exists()).toBe(false)
      wrapper.unmount()
    })

    it('keeps every body row aligned with the visible header count', async () => {
      const wrapper = mountTable()
      const headerCount = wrapper.findAll('thead th').length
      const first = wrapper.findAll('tbody tr').find((tr) => tr.find('td.col-date').exists())
      expect(first.findAll('td')).toHaveLength(headerCount)
      wrapper.unmount()
    })

    it('does not force a 50vh minimum and scrolls only inside a labelled region', () => {
      const wrapper = mountTable()
      const scroll = wrapper.get('.table-scroll')
      expect(scroll.classes().join(' ')).not.toMatch(/min-h-\[50vh\]|min-h-\[55vh\]/)
      expect(scroll.attributes('role')).toBe('region')
      expect(scroll.attributes('aria-label')).toBe('Transactions table')
      expect(wrapper.get('.table-shell').classes()).not.toContain('overflow-hidden')
      wrapper.unmount()
    })

    it('right-aligns amounts with tabular numerals and truncates text with the full value on hover', () => {
      const wrapper = mountTable()
      expect(wrapper.get('th.col-amount').classes()).toContain('text-right')
      const titles = wrapper
        .findAll('td.col-description .truncate')
        .map((node) => node.attributes('title'))
      expect(titles.some((title) => title?.includes('A very long description'))).toBe(true)
    })

    it('labels edit fields and keeps Save/Cancel as non-submitting buttons', async () => {
      const wrapper = mountTable()
      const edit = wrapper.findAll('button').find((b) => b.text() === 'Edit')
      await edit.trigger('click')
      await flushPromises()
      ;['Date', 'Amount', 'Description', 'Category', 'Merchant'].forEach((label) => {
        expect(wrapper.find(`input[aria-label="${label}"]`).exists(), label).toBe(true)
      })
      const save = wrapper.findAll('button').find((b) => b.text() === 'Save')
      const cancel = wrapper.findAll('button').find((b) => b.text() === 'Cancel')
      expect(save.attributes('type')).toBe('button')
      expect(cancel.attributes('type')).toBe('button')
      wrapper.unmount()
    })
  })

  describe('reporting flow and scrolling', () => {
    const row = (id, over = {}) => ({
      transaction_id: id,
      date: '2026-10-13',
      amount: 10,
      description: `Row ${id}`,
      category: 'Food',
      merchant_name: 'Shop',
      account_name: 'Checking',
      institution_name: 'Bank',
      tags: [],
      ...over,
    })

    it('marks transfers, refunds, debt payments and unreviewed credits without badging ordinary rows', async () => {
      const wrapper = mount(UpdateTransactionsTable, {
        props: {
          transactions: [
            row('a', { reporting_flow_kind: 'transfer' }),
            row('b', { reporting_flow_kind: 'refund' }),
            row('c', { reporting_flow_kind: 'debt_settlement' }),
            row('d', { reporting_flow_kind: 'unclassified' }),
            row('e', { reporting_flow_kind: 'expense' }),
            row('f', { reporting_flow_kind: 'income' }),
          ],
          currentPage: 1,
          pageSize: 10,
        },
      })
      await flushPromises()
      expect(wrapper.get('[data-testid="flow-badge-a"]').text()).toBe('Transfer')
      expect(wrapper.get('[data-testid="flow-badge-b"]').text()).toBe('Refund')
      expect(wrapper.get('[data-testid="flow-badge-c"]').text()).toBe('Debt payment')
      expect(wrapper.get('[data-testid="flow-badge-d"]').text()).toBe('Needs review')
      expect(wrapper.get('[data-testid="flow-badge-d"]').attributes('title')).toContain(
        'Not counted',
      )
      expect(wrapper.find('[data-testid="flow-badge-e"]').exists()).toBe(false)
      expect(wrapper.find('[data-testid="flow-badge-f"]').exists()).toBe(false)
    })

    it('lets a paginated page scroll with the document: horizontal overflow only, no inner height cap', async () => {
      const wrapper = mount(UpdateTransactionsTable, {
        props: {
          transactions: Array.from({ length: 10 }, (_, i) => row(`p${i}`)),
          currentPage: 1,
          pageSize: 10,
        },
      })
      await flushPromises()
      const region = wrapper.get('[role="region"][aria-label="Transactions table"]')
      expect(region.classes()).toContain('overflow-x-auto')
      expect(region.classes().join(' ')).not.toMatch(/max-h-/)
      expect(wrapper.get('thead').classes()).not.toContain('sticky')
    })

    it('keeps column sort keyboard-accessible with aria-sort', async () => {
      const wrapper = mount(UpdateTransactionsTable, {
        props: { transactions: [row('s1'), row('s2')], currentPage: 1, pageSize: 10 },
      })
      await flushPromises()
      const amountHeader = wrapper.get('th[aria-sort]:has([data-testid="sort-amount"])')
      expect(amountHeader.attributes('aria-sort')).toBe('none')
      await wrapper.get('[data-testid="sort-amount"]').trigger('click')
      expect(wrapper.get('th:has([data-testid="sort-amount"])').attributes('aria-sort')).toBe(
        'descending',
      )
      expect(wrapper.get('[data-testid="sort-amount"]').element.tagName).toBe('BUTTON')
    })
  })

  describe('server-filtered mode', () => {
    const rows = [
      {
        transaction_id: 'a',
        date: '2024-01-01',
        amount: 10,
        description: 'Alpha',
        category: 'Food',
      },
      {
        transaction_id: 'b',
        date: '2024-01-02',
        amount: 20,
        description: 'Beta',
        category: 'Bills',
      },
      {
        transaction_id: 'c',
        date: '2024-01-03',
        amount: 30,
        description: 'Gamma',
        category: 'Bills',
      },
    ]
    const mountServerFiltered = (props = {}) =>
      mount(UpdateTransactionsTable, {
        props: { transactions: rows, currentPage: 2, pageSize: 2, serverFiltered: true, ...props },
        global: { stubs: ['Modal', 'FuzzyDropdown'] },
      })

    it('renders the page it is given without re-slicing or narrowing it', async () => {
      const wrapper = mountServerFiltered()
      await flushPromises()
      wrapper.vm.selectedPrimaryCategory = 'Food'
      await flushPromises()

      const displayed = wrapper.vm.displayTransactions.filter((tx) => !tx._placeholder)
      expect(displayed.map((tx) => tx.transaction_id).sort()).toEqual(['a', 'b', 'c'])
    })

    it('reports column and category filters as server parameters instead of applying them', async () => {
      const wrapper = mountServerFiltered()
      await flushPromises()

      wrapper.vm.selectFilterField('description')
      wrapper.vm.fieldSearch = ' alpha '
      wrapper.vm.addFieldFilter()
      wrapper.vm.selectedPrimaryCategory = 'Food'
      await flushPromises()

      const emitted = wrapper.emitted('update:filters')
      expect(emitted.at(-1)[0]).toEqual({ filter_description: 'alpha', category_primary: 'Food' })

      wrapper.vm.removeFilterTag('field:description')
      await flushPromises()
      expect(wrapper.emitted('update:filters').at(-1)[0]).toEqual({ category_primary: 'Food' })
    })

    it('does not emit filters in standalone mode', async () => {
      const wrapper = mount(UpdateTransactionsTable, {
        props: { transactions: rows },
        global: { stubs: ['Modal', 'FuzzyDropdown'] },
      })
      wrapper.vm.selectedPrimaryCategory = 'Food'
      await flushPromises()
      expect(wrapper.emitted('update:filters')).toBeUndefined()
    })
  })
})
