// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import Dashboard from '../Dashboard.vue'

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
    filteredTransactions: ref([]),
    sortKey: ref(null),
    sortOrder: ref(1),
    setSort: vi.fn(),
    changePage: vi.fn(),
  }),
}))

vi.mock('@/api/transactions', () => ({
  fetchTransactions: vi.fn().mockResolvedValue({ transactions: [] }),
}))

// Tests for Dashboard.vue date range behavior

describe('Dashboard.vue', () => {
  it('clears selected categories when date range changes', async () => {
    const wrapper = shallowMount(Dashboard, {
      global: {
        stubs: {
          AppLayout: true,
          BasePageLayout: true,
          DailyNetChart: true,
          CategoryBreakdownChart: true,
          ChartWidgetTopBar: true,
          ChartControls: true,
          DateRangeSelector: true,
          AccountsTable: true,
          TransactionsTable: true,
          PaginationControls: true,
          TransactionModal: true,
          TopAccountSnapshot: true,
          GroupedCategoryDropdown: true,
          FinancialSummary: true,
          SpendingInsights: true,
        },
      },
    })

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
})
