import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import {
  fetchAccountActivityBreakdown,
  fetchNetChanges,
  rangeToDates,
  toLocalIsoDate,
} from '../accounts'

vi.mock('axios', () => ({ default: { get: vi.fn() } }))

describe('rangeToDates', () => {
  it('returns exactly N inclusive local days ending today', () => {
    const now = new Date(2026, 9, 14, 23, 30) // Oct 14 late evening local time
    expect(rangeToDates('30d', now)).toEqual({ start: '2026-09-15', end: '2026-10-14' })
    expect(rangeToDates('7d', now)).toEqual({ start: '2026-10-08', end: '2026-10-14' })
    expect(rangeToDates('365d', now)).toEqual({ start: '2025-10-15', end: '2026-10-14' })
  })

  it('does not shift to the next UTC day for late-evening local times', () => {
    const lateLocal = new Date(2026, 0, 31, 23, 59)
    expect(rangeToDates('1d', lateLocal)).toEqual({ start: '2026-01-31', end: '2026-01-31' })
    expect(toLocalIsoDate(lateLocal)).toBe('2026-01-31')
  })

  it('crosses month and year boundaries and falls back to 30 days', () => {
    expect(rangeToDates('3d', new Date(2026, 0, 1))).toEqual({
      start: '2025-12-30',
      end: '2026-01-01',
    })
    expect(rangeToDates('bogus', new Date(2026, 2, 31))).toEqual({
      start: '2026-03-02',
      end: '2026-03-31',
    })
  })
})

describe('account activity api', () => {
  beforeEach(() => axios.get.mockReset())

  it('joins account ids and passes inclusive dates to the breakdown endpoint', async () => {
    axios.get.mockResolvedValue({ data: { status: 'success', accounts: [] } })
    await fetchAccountActivityBreakdown({
      start_date: '2026-09-01',
      end_date: '2026-09-30',
      account_ids: ['a', 'b'],
    })
    expect(axios.get).toHaveBeenCalledWith('/api/accounts/activity_breakdown', {
      params: { start_date: '2026-09-01', end_date: '2026-09-30', account_ids: 'a,b' },
    })
  })

  it('keeps the movement fields from net_changes and normalizes the legacy shape', async () => {
    axios.get.mockResolvedValueOnce({
      data: {
        status: 'success',
        data: { income: 1, expense: 2, net: -1, money_in: 1, money_out: 2, net_movement: -1 },
      },
    })
    expect((await fetchNetChanges('a', {})).data.money_in).toBe(1)
    axios.get.mockResolvedValueOnce({ data: { net_change: 5 } })
    expect((await fetchNetChanges('a', {})).data).toMatchObject({ net: 5, balance_change: 5 })
  })
})
