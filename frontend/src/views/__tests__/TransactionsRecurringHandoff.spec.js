// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, ref } from 'vue'
import Transactions from '../Transactions.vue'

const useTransactionsMock = vi.fn()

vi.mock('@/composables/useTransactions.js', () => ({
  useTransactions: (...args) => useTransactionsMock(...args),
}))
vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
vi.mock('@/services/api', () => ({
  default: {
    getTransactionInsights: vi.fn().mockResolvedValue({ status: 'success', data: null }),
    getAccounts: vi.fn().mockResolvedValue({ accounts: [] }),
  },
}))

const openFromTransaction = vi.fn()

/** Child stub exposing the same public API as the real recurring section. */
const RecurringStub = defineComponent({
  name: 'RecurringTransactionSection',
  setup(_, { expose }) {
    expose({ openFromTransaction })
    return () => h('div', { 'data-testid': 'recurring-stub' })
  },
})

/** Table stub that lets the test raise the same event the real table emits. */
const TableStub = defineComponent({
  name: 'UpdateTransactionsTable',
  emits: ['editRecurringFromTransaction'],
  setup(_, { emit }) {
    return () =>
      h('button', {
        'data-testid': 'recur-btn',
        onClick: () => emit('editRecurringFromTransaction', { transaction_id: 'tx-1', amount: 12 }),
      })
  },
})

/** Layout stub that only renders the active tab's slot, like the real layout. */
const LayoutStub = defineComponent({
  props: ['modelValue', 'tabs'],
  setup(props, { slots }) {
    return () =>
      h('div', [
        h('span', { 'data-testid': 'active-tab' }, props.modelValue),
        slots.header?.(),
        slots[props.modelValue]?.(),
      ])
  },
})

function mountView() {
  useTransactionsMock.mockReturnValue({
    searchQuery: ref(''),
    currentPage: ref(1),
    totalPages: ref(1),
    totalCount: ref(1),
    filteredTransactions: ref([{ transaction_id: 'tx-1', amount: 12 }]),
    paginatedTransactions: ref([{ transaction_id: 'tx-1', amount: 12 }]),
    changePage: vi.fn(),
    setPage: vi.fn(),
    sortKey: ref(null),
    sortOrder: ref(1),
    setSort: vi.fn(),
    isLoading: ref(false),
    error: ref(null),
    fetchTransactions: vi.fn(),
  })
  return shallowMount(Transactions, {
    global: {
      stubs: {
        Card: { template: '<div><slot /></div>' },
        PageHeader: { template: '<header />' },
        PaginationControls: true,
        UiButton: { template: '<button><slot /></button>' },
        TabbedPageLayout: LayoutStub,
        UpdateTransactionsTable: TableStub,
        RecurringTransactionSection: RecurringStub,
      },
    },
  })
}

describe('Transactions -> Recurring hand-off', () => {
  beforeEach(() => vi.clearAllMocks())

  it('switches to the Recurring tab and calls the child openFromTransaction API', async () => {
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('[data-testid="active-tab"]').text()).toBe('Activity')
    expect(wrapper.find('[data-testid="recurring-stub"]').exists()).toBe(false)

    await wrapper.get('[data-testid="recur-btn"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-testid="active-tab"]').text()).toBe('Recurring')
    expect(openFromTransaction).toHaveBeenCalledTimes(1)
    expect(openFromTransaction).toHaveBeenCalledWith({ transaction_id: 'tx-1', amount: 12 })
  })

  it('labels the third tab Transfer Review while keeping the Scanner slot', () => {
    const wrapper = mountView()
    const layout = wrapper.findComponent(LayoutStub)
    expect(layout.props('tabs')).toEqual([
      'Activity',
      'Recurring',
      { label: 'Transfer Review', slot: 'Scanner' },
    ])
  })
})
