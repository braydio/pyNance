// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import Investments from '../Investments.vue'

const here = path.dirname(fileURLToPath(import.meta.url))

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

  it('shows the portfolio summary before maintenance and keeps refresh/link reachable', async () => {
    apiMocks.fetchHoldings.mockResolvedValue({
      data: [{ account_id: 'acc-1', security_id: 's1', institution_value: 150, quantity: 1 }],
    })
    const wrapper = mountInvestments()
    await flushPromises()

    const html = wrapper.html()
    expect(html.indexOf('data-testid="portfolio-summary"')).toBeLessThan(
      html.indexOf('id="maintenance"'),
    )
    expect(html.indexOf('id="holdings"')).toBeLessThan(html.indexOf('id="maintenance"'))
    expect(wrapper.get('[data-testid="portfolio-summary"]').text()).toContain('$150.00')
    expect(wrapper.text()).toContain('Refresh Investments')
    expect(wrapper.text()).toContain('Link New Investments Account')

    const labels = wrapper.findAll('.section-subnav__link').map((node) => node.text())
    expect(labels).toEqual(['Portfolio', 'Holdings', 'Performance', 'Activity', 'Manage'])
  })

  it('collapses transaction filters behind a disclosure with an active count', async () => {
    const wrapper = mountInvestments()
    await flushPromises()

    const disclosure = wrapper.get('[data-testid="tx-filters-disclosure"]')
    expect(disclosure.attributes('open')).toBeUndefined()
    await wrapper.get('[data-testid="tx-filter-type"]').setValue('buy')
    expect(disclosure.get('summary').text()).toContain('(1)')
  })
})

describe('Investments UI details', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    apiMocks.fetchHoldings.mockResolvedValue({ data: [] })
    apiMocks.fetchInvestmentAccounts.mockResolvedValue({
      data: [{ account_id: 'acc-1', name: 'Brokerage', institution_name: 'Fidelity' }],
    })
    apiMocks.fetchInvestmentTransactions.mockResolvedValue(txPayload)
    apiMocks.refreshInvestmentsAll.mockResolvedValue({ summary: {} })
  })

  it('links holding account rows to their detail panels with truthful aria state', async () => {
    apiMocks.fetchHoldings.mockResolvedValue({
      data: [
        {
          account_id: 'acc-1',
          security_id: 's1',
          institution_value: 150,
          quantity: 1,
          security: {
            name: 'A very long security name that should wrap',
            ticker_symbol: 'AAA',
            price: 150,
          },
        },
        {
          account_id: 'acc-2',
          security_id: 's2',
          institution_value: 50,
          quantity: 2,
          security: { name: 'Beta', ticker_symbol: 'BBB', price: 25 },
        },
      ],
    })
    const wrapper = mountInvestments()
    await flushPromises()

    const toggle = wrapper.get('[data-testid="holding-toggle-acc-1"]')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    const panel = wrapper.get(`#${toggle.attributes('aria-controls')}`)
    expect(panel.text()).toContain('AAA')
    expect(panel.find('.name-clip').attributes('title')).toContain('very long security name')
  })

  it('scrolls tables inside labelled regions instead of the page', async () => {
    apiMocks.fetchHoldings.mockResolvedValue({
      data: [{ account_id: 'acc-1', security_id: 's1', institution_value: 150, quantity: 1 }],
    })
    const wrapper = mountInvestments()
    await flushPromises()
    const region = wrapper.get('.holdings-table')
    expect(region.attributes('role')).toBe('region')
    expect(region.attributes('aria-label')).toBe('Holdings')
    expect(region.attributes('tabindex')).toBe('0')
  })

  it('renders a real Link button from the launcher slot', async () => {
    const wrapper = mount(Investments, {
      global: {
        stubs: {
          BasePageLayout: { template: '<div><slot /></div>' },
          PageHeader: { template: '<header />' },
          PortfolioAllocationChart: { template: '<div />' },
          LinkProviderLauncher: {
            template:
              '<div><slot :link-plaid="() => {}" :loading="false" :is-disabled="false" error-message="" status-message="" /></div>',
          },
        },
      },
    })
    await flushPromises()
    const button = wrapper.get('[data-testid="link-investments"]')
    expect(button.text()).toBe('Link investments account')
    expect(button.attributes('type')).toBe('button')
  })

  it('resets transaction filters from the disclosure and uses shared control classes', async () => {
    const wrapper = mountInvestments()
    await flushPromises()
    const type = wrapper.get('[data-testid="tx-filter-type"]')
    expect(type.classes()).toContain('input')
    expect(wrapper.get('[data-testid="tx-filter-account"]').classes()).toContain('select')
    const reset = wrapper.get('[data-testid="tx-filter-reset"]')
    expect(reset.attributes('disabled')).toBeDefined()
    await type.setValue('buy')
    expect(reset.attributes('disabled')).toBeUndefined()
    await reset.trigger('click')
    expect(type.element.value).toBe('')
    expect(wrapper.find('[data-testid="tx-filter-count"]').exists()).toBe(false)
  })

  it('has no hardcoded gray/white colors in the page styles', () => {
    const source = readFileSync(path.resolve(here, '../Investments.vue'), 'utf-8')
    expect(source).not.toMatch(/#6b7280|#94a3b8|color:\s*#fff\b/i)
  })
})
