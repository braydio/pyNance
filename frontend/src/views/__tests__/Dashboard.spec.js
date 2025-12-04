// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Dashboard from '../Dashboard.vue'
import { fetchTransactions } from '@/api/transactions'

// Mock modules used by Dashboard.vue
vi.mock('@/services/api', () => ({
  default: { fetchNetAssets: vi.fn().mockResolvedValue({ status: 'success', data: [] }) },
}))

vi.mock('@/api/categories', () => ({
  fetchCategoryTree: vi.fn().mockResolvedValue({ status: 'success', data: [] }),
}))

vi.mock('@/composables/useTransactions.js', () => ({
  useTransactions: () => ({
    searchQuery: ref(''),
    currentPage: ref(1),
    totalPages: ref(1),
    totalCount: ref(0),
    filteredTransactions: ref([]),
    sortKey: ref(null),
    sortOrder: ref(1),
    setSort: vi.fn(),
    setPage: vi.fn(),
    changePage: vi.fn(),
  }),
}))

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
}))

vi.mock('@/composables/useAccountGroups', () => ({
  useAccountGroups: () => ({ groups: ref([]), activeGroupId: ref(null) }),
}))

let receivedProps = null
const TopAccountSnapshotStub = {
  name: 'TopAccountSnapshot',
  template: '<div class="tas-stub"></div>',
  props: {
    groups: { type: Array, default: () => [] },
    modelValue: { type: Array, default: () => [] },
  },
  setup(props) {
    receivedProps = props
  },
}

const PassThrough = { template: '<div><slot /></div>' }

// Tests for Dashboard.vue date range behavior

describe('Dashboard.vue', () => {
  it('clears selected categories when date range changes', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: true,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    expect(receivedProps).not.toBeNull()
    expect(receivedProps.groups).toBeDefined()

    wrapper.vm.allCategoryIds = ['a', 'b', 'c', 'd', 'e', 'f']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['a', 'b', 'c', 'd', 'e'])

    wrapper.vm.dateRange.start = '2024-01-01'
    wrapper.vm.dateRange.end = '2024-01-31'
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual([])

    wrapper.vm.allCategoryIds = ['x', 'y', 'z']
    await nextTick()
    expect(wrapper.vm.catSelected).toEqual(['x', 'y', 'z'])
  })

  it('uses the clicked bar date when opening the daily transactions modal', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: PassThrough,
          BasePageLayout: PassThrough,
          DailyNetChart: true,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartDetailsSidebar: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: TopAccountSnapshotStub,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

    const barLabel = '2024-06-10T00:00:00'
    await wrapper.vm.onNetBarClick(barLabel)

    expect(fetchTransactions).toHaveBeenCalledWith({
      start_date: '2024-06-10',
      end_date: '2024-06-10',
      page: 1,
      page_size: 1000,
    })
    expect(wrapper.vm.dailyModalSubtitle).toBe('2024-06-10')
    expect(wrapper.vm.showDailyModal).toBe(true)
  })
})
