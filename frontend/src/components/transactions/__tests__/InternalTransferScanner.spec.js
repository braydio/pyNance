// @vitest-environment jsdom
import { beforeEach, describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import InternalTransferScanner from '../InternalTransferScanner.vue'
import api from '@/services/api.js'

vi.mock('@/services/api.js', () => ({
  default: { scanInternalTransfers: vi.fn(), updateTransaction: vi.fn() },
}))

const pair = {
  pair_id: 't1~t2',
  left: {
    transaction_id: 't1',
    date: '2026-10-15',
    account_label: 'Bank / Checking',
    merchant: 'Transfer to savings',
    amount: -50,
  },
  right: {
    transaction_id: 't2',
    date: '2026-10-15',
    account_label: 'Bank / Savings',
    merchant: 'Transfer from checking',
    amount: 50,
  },
  evidence: {
    amount_gap_cents: 0,
    day_gap: 0,
    shared_tokens: ['transfer'],
    transfer_keyword: true,
    low_confidence: false,
  },
  confidence_label: 'strong',
}
const weakPair = {
  ...pair,
  pair_id: 't3~t4',
  left: { ...pair.left, transaction_id: 't3' },
  right: { ...pair.right, transaction_id: 't4' },
  evidence: {
    amount_gap_cents: 0,
    day_gap: 2,
    shared_tokens: [],
    transfer_keyword: false,
    low_confidence: true,
  },
  confidence_label: 'review',
}
const response = (pairs, extra = {}) => ({
  status: 'success',
  pairs,
  range: { start: '2026-07-20', end: '2026-10-17' },
  truncated: false,
  ...extra,
})

async function scanned(pairs = [pair], extra = {}) {
  api.scanInternalTransfers.mockResolvedValue(response(pairs, extra))
  const wrapper = mount(InternalTransferScanner)
  await wrapper.get('button').trigger('click')
  await flushPromises()
  return wrapper
}

describe('InternalTransferScanner (Transfer Review)', () => {
  beforeEach(() => vi.clearAllMocks())

  it('explains its purpose and uses themed, non-submitting buttons', async () => {
    const wrapper = await scanned()
    expect(wrapper.text()).toContain('Transfer Review')
    expect(wrapper.text()).toContain('Nothing changes until you confirm')
    expect(wrapper.html()).not.toContain('text-gray-500')
    expect(wrapper.html()).toContain('text-muted')
    wrapper.findAll('button').forEach((b) => expect(b.attributes('type')).toBe('button'))
  })

  it('shows the scanned range, count, paired cards and evidence instead of a raw score', async () => {
    const wrapper = await scanned([pair, weakPair])
    expect(wrapper.get('[data-testid="scan-summary"]').text()).toContain('2026-07-20 to 2026-10-17')
    expect(wrapper.get('[data-testid="scan-summary"]').text()).toContain('2 pairs to review')
    const card = wrapper.get('[data-testid="pair-t1~t2"]')
    expect(card.text()).toContain('Money out')
    expect(card.text()).toContain('Bank / Checking')
    expect(card.text()).toContain('-$50.00')
    expect(card.text()).toContain('+$50.00')
    expect(card.text()).toContain('Strong match')
    expect(card.text()).toContain('Exact same amount')
    expect(card.text()).toContain('Shared words: transfer')
    expect(wrapper.get('[data-testid="pair-t3~t4"]').text()).toContain('Needs your review')
    expect(wrapper.get('[data-testid="pair-t3~t4"]').text()).toContain('Posted 2 days apart')
    expect(wrapper.text()).not.toMatch(/match score|time delta/i)
  })

  it('does not mutate anything on scan, only on explicit confirmation', async () => {
    await scanned()
    expect(api.updateTransaction).not.toHaveBeenCalled()
  })

  it('confirms a pair with both ids, then shows the done state', async () => {
    api.updateTransaction.mockResolvedValue({ status: 'success' })
    const wrapper = await scanned()
    const confirmButton = wrapper.findAll('button').find((b) => b.text() === 'Confirm Pair')
    await confirmButton.trigger('click')
    await flushPromises()
    expect(api.updateTransaction).toHaveBeenCalledWith({
      transaction_id: 't1',
      is_internal: true,
      counterpart_transaction_id: 't2',
      flag_counterpart: true,
    })
    expect(wrapper.find('[data-testid="pair-t1~t2"]').exists()).toBe(false)
    expect(wrapper.get('[data-testid="confirmed-count"]').text()).toContain('1 pair confirmed')
    expect(wrapper.text()).toContain('No transfer pairs left to review')
  })

  it('keeps the pair and shows an error when confirmation fails', async () => {
    api.updateTransaction.mockRejectedValue({
      response: { data: { message: 'Transfer legs must move money' } },
    })
    const wrapper = await scanned()
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Confirm Pair')
      .trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="pair-t1~t2"]').exists()).toBe(true)
    expect(wrapper.get('[role="alert"]').text()).toContain('Transfer legs must move money')
  })

  it('"Not a Transfer" hides the pair without calling the API', async () => {
    const wrapper = await scanned([pair, weakPair])
    await wrapper
      .get('[data-testid="pair-t1~t2"]')
      .findAll('button')
      .find((b) => b.text() === 'Not a Transfer')
      .trigger('click')
    expect(wrapper.find('[data-testid="pair-t1~t2"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="pair-t3~t4"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="scan-summary"]').text()).toContain('1 dismissed')
    expect(api.updateTransaction).not.toHaveBeenCalled()
  })

  it('tells the user when results were truncated', async () => {
    const wrapper = await scanned([pair], { truncated: true })
    expect(wrapper.get('[data-testid="scan-truncated"]').text()).toContain('limited')
  })

  it('shows an error when scanning fails instead of claiming there are no transfers', async () => {
    api.scanInternalTransfers.mockRejectedValueOnce(new Error('down'))
    const wrapper = mount(InternalTransferScanner)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Unable to scan')
    expect(wrapper.text()).not.toContain('No transfer pairs left')
  })

  it('explains a missing server owner configuration', async () => {
    api.scanInternalTransfers.mockRejectedValueOnce({
      response: { data: { code: 'owner_not_configured' } },
    })
    const wrapper = mount(InternalTransferScanner)
    await wrapper.get('button').trigger('click')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('not set up on this server')
  })
})
