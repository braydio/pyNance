import { describe, expect, it, vi } from 'vitest'
import { loadDayTransactions } from '../dailyModal'

const makeRows = (n, offset = 0) =>
  Array.from({ length: n }, (_, i) => ({ transaction_id: `t${offset + i}` }))

describe('loadDayTransactions', () => {
  it('requests the day with transfers included and stops when everything is loaded', async () => {
    const fetcher = vi.fn().mockResolvedValue({ transactions: makeRows(3), total: 3 })
    const result = await loadDayTransactions(fetcher, '2026-10-13')
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(fetcher).toHaveBeenCalledWith({
      start_date: '2026-10-13',
      end_date: '2026-10-13',
      page: 1,
      page_size: 1000,
      include_transfers: true,
    })
    expect(result).toMatchObject({ total: 3, partial: false })
  })

  it('pages through 1,001 rows rather than trusting the first 1,000', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ transactions: makeRows(1000), total: 1001 })
      .mockResolvedValueOnce({ transactions: makeRows(1, 1000), total: 1001 })
    const result = await loadDayTransactions(fetcher, '2026-10-13')
    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(result.rows).toHaveLength(1001)
    expect(result.partial).toBe(false)
  })

  it('reports a bounded, partial load instead of claiming the whole day', async () => {
    const fetcher = vi.fn().mockResolvedValue({ transactions: makeRows(10), total: 100 })
    const result = await loadDayTransactions(fetcher, '2026-10-13', { pageSize: 10, maxPages: 3 })
    expect(fetcher).toHaveBeenCalledTimes(3)
    expect(result).toMatchObject({ total: 100, partial: true })
    expect(result.rows).toHaveLength(30)
  })

  it('returns no rows for an empty day and propagates fetch errors', async () => {
    const empty = await loadDayTransactions(
      vi.fn().mockResolvedValue({ transactions: [], total: 0 }),
      '2026-10-13',
    )
    expect(empty).toEqual({ rows: [], total: 0, partial: false })
    await expect(
      loadDayTransactions(vi.fn().mockRejectedValue(new Error('down')), '2026-10-13'),
    ).rejects.toThrow('down')
  })
})
