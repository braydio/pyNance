// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import Investments from '../Investments.vue'

const apiMocks = vi.hoisted(() => ({
  fetchHoldings: vi.fn(),
  refreshInvestmentsAll: vi.fn(),
  fetchInvestmentAccounts: vi.fn(),
  fetchInvestmentTransactions: vi.fn(),
}))

vi.mock('@/api/investments', () => ({
  fetchHoldings: (...args) => apiMocks.fetchHoldings(...args),
  refreshInvestmentsAll: (...args) => apiMocks.refreshInvestmentsAll(...args),
  fetchInvestmentAccounts: (...args) => apiMocks.fetchInvestmentAccounts(...args),
  fetchInvestmentTransactions: (...args) => apiMocks.fetchInvestmentTransactions(...args),
}))

function ensureMockStorage() {
  if (typeof localStorage !== 'undefined' && typeof localStorage.clear === 'function') return
  let store = {}
  const storage = {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, val) => {
      store[key] = String(val)
    },
    removeItem: (key) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
  Object.defineProperty(globalThis, 'localStorage', { value: storage, writable: true })
}

ensureMockStorage()

function mountInvestments() {
  return mount(Investments, {
    global: {
      stubs: {
        BasePageLayout: { template: '<div><slot /></div>' },
        Card: { template: '<div><slot /></div>' },
        PageHeader: { template: '<header><slot name="title" /><slot name="subtitle" /></header>' },
        PortfolioAllocationChart: { template: '<div />' },
        LinkProviderLauncher: { template: '<button />' },
      },
    },
  })
}

const txPayload = {
  transactions: [
    {
      investment_transaction_id: 'tx-1',
      date: '2026-01-01',
      account_id: 'acc-1',
      security_id: 'sec-1',
      name: 'Buy',
      quantity: 1,
      price: 10,
      amount: 10,
    },
  ],
  total: 25,
}
const expectedUserId = import.meta.env.VITE_USER_ID_PLAID || import.meta.env.VITE_USER_ID || ''

describe('Investments.vue transaction filters', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()

    apiMocks.fetchHoldings.mockResolvedValue({ data: [] })
    apiMocks.fetchInvestmentAccounts.mockResolvedValue({
      data: [
        {
          account_id: 'acc-1',
          name: 'Brokerage',
          institution_name: 'Fidelity',
        },
      ],
    })
    apiMocks.fetchInvestmentTransactions.mockResolvedValue(txPayload)
    apiMocks.refreshInvestmentsAll.mockResolvedValue({ summary: {} })
  })

  it('sends backend-aligned query params when transaction filters change', async () => {
    const wrapper = mountInvestments()
    await flushPromises()

    await wrapper.find('[data-testid="tx-filter-account"]').setValue('acc-1')
    await wrapper.find('[data-testid="tx-filter-security-id"]').setValue('sec-123')
    await wrapper.find('[data-testid="tx-filter-type"]').setValue('buy')
    await wrapper.find('[data-testid="tx-filter-subtype"]').setValue('dividend')
    await wrapper.find('[data-testid="tx-filter-start-date"]').setValue('2025-01-01')
    await wrapper.find('[data-testid="tx-filter-end-date"]').setValue('2025-01-31')
    await flushPromises()

    expect(apiMocks.fetchInvestmentTransactions).toHaveBeenLastCalledWith(
      1,
      10,
      expect.objectContaining({
        user_id: expectedUserId,
        account_id: 'acc-1',
        security_id: 'sec-123',
        type: 'buy',
        subtype: 'dividend',
        start_date: '2025-01-01',
        end_date: '2025-01-31',
      }),
    )
  })

  it('restores persisted filter selections from localStorage on mount and remount', async () => {
    localStorage.setItem(
      'investments.transactionFilters',
      JSON.stringify({
        account_id: 'acc-1',
        security_id: 'sec-42',
        type: 'sell',
        subtype: 'withdrawal',
        start_date: '2024-05-01',
        end_date: '2024-05-31',
      }),
    )

    const wrapper = mountInvestments()
    await flushPromises()

    expect(apiMocks.fetchInvestmentTransactions).toHaveBeenCalledWith(
      1,
      10,
      expect.objectContaining({
        user_id: expectedUserId,
        account_id: 'acc-1',
        security_id: 'sec-42',
        type: 'sell',
        subtype: 'withdrawal',
        start_date: '2024-05-01',
        end_date: '2024-05-31',
      }),
    )
    expect(wrapper.find('[data-testid="tx-filter-security-id"]').element.value).toBe('sec-42')

    wrapper.unmount()
    apiMocks.fetchInvestmentTransactions.mockClear()

    const remount = mountInvestments()
    await flushPromises()
    expect(apiMocks.fetchInvestmentTransactions).toHaveBeenCalledWith(
      1,
      10,
      expect.objectContaining({
        user_id: expectedUserId,
        account_id: 'acc-1',
        security_id: 'sec-42',
        type: 'sell',
        subtype: 'withdrawal',
        start_date: '2024-05-01',
        end_date: '2024-05-31',
      }),
    )
    remount.unmount()
  })

  it('resets pagination to page 1 when filters change after paging', async () => {
    const wrapper = mountInvestments()
    await flushPromises()

    await wrapper.find('.pager .btn:last-child').trigger('click')
    await flushPromises()

    expect(apiMocks.fetchInvestmentTransactions).toHaveBeenLastCalledWith(
      2,
      10,
      expect.objectContaining({ user_id: expectedUserId }),
    )

    await wrapper.find('[data-testid="tx-filter-type"]').setValue('buy')
    await flushPromises()

    expect(apiMocks.fetchInvestmentTransactions).toHaveBeenLastCalledWith(
      1,
      10,
      expect.objectContaining({
        user_id: expectedUserId,
        type: 'buy',
      }),
    )
  })

  it('shows aggregate account rows before holding details when multiple accounts are in scope', async () => {
    apiMocks.fetchHoldings.mockResolvedValue({
      data: [
        {
          account_id: 'acc-1',
          security_id: 'sec-1',
          quantity: 2,
          institution_value: 50,
          security: { ticker_symbol: 'AAA', name: 'Alpha', price: 25 },
        },
        {
          account_id: 'acc-1',
          security_id: 'sec-2',
          quantity: 1,
          institution_value: 30,
          security: { ticker_symbol: 'BBB', name: 'Beta', price: 30 },
        },
        {
          account_id: 'acc-2',
          security_id: 'sec-3',
          quantity: 4,
          institution_value: 80,
          security: { ticker_symbol: 'CCC', name: 'Gamma', price: 20 },
        },
      ],
    })
    apiMocks.fetchInvestmentAccounts.mockResolvedValue({
      data: [
        { account_id: 'acc-1', name: 'Brokerage 1', institution_name: 'Fidelity' },
        { account_id: 'acc-2', name: 'Brokerage 2', institution_name: 'Robinhood' },
      ],
    })

    const wrapper = mountInvestments()
    await flushPromises()

    const summaryRows = wrapper.findAll('.holdings-summary-row')
    expect(summaryRows).toHaveLength(2)
    expect(wrapper.text()).toContain('Multiple accounts are selected')
    expect(wrapper.text()).not.toContain('AAAAlpha')

    await summaryRows[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('AAA')
    expect(wrapper.text()).toContain('Alpha')
  })
})
