import { beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import { fetchInvestmentTransactions } from '../investments'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
  },
}))

describe('fetchInvestmentTransactions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    axios.get.mockResolvedValue({ data: { transactions: [], total: 0 } })
  })

  it('sends only backend-supported query params for transaction filters', async () => {
    await fetchInvestmentTransactions(2, 50, {
      user_id: 'user-1',
      account_id: 'acc-1',
      security_id: 'sec-1',
      type: 'buy',
      subtype: 'dividend',
      start_date: '2025-01-01',
      end_date: '2025-01-31',
      ignored_filter: 'noop',
    })

    expect(axios.get).toHaveBeenCalledWith('/api/investments/transactions', {
      params: {
        page: 2,
        page_size: 50,
        user_id: 'user-1',
        account_id: 'acc-1',
        security_id: 'sec-1',
        type: 'buy',
        subtype: 'dividend',
        start_date: '2025-01-01',
        end_date: '2025-01-31',
      },
    })
  })
})
