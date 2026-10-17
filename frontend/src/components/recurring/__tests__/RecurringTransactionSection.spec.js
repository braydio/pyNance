// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import RecurringTransactionSection from '../RecurringTransactionSection.vue'
import * as recurringApi from '@/api/recurring'
import api from '@/services/api'

vi.mock('@/api/recurring', () => ({
  getRecurringStreams: vi.fn(),
  getRecurringCandidates: vi.fn(),
  scanRecurring: vi.fn(),
  createRecurringStream: vi.fn(),
  updateRecurringStream: vi.fn(),
  decideRecurringStream: vi.fn(),
}))
vi.mock('@/services/api', () => ({ default: { getAccounts: vi.fn() } }))

const accounts = [
  { account_id: 'chk', name: 'Checking' },
  { account_id: 'sav', name: 'Savings' },
]
const candidate = {
  stream_id: 'c1',
  account_id: 'chk',
  display_name: 'Duke Energy',
  status: 'proposed',
  source: 'detected',
  cadence: 'monthly',
  amount_mode: 'variable',
  amount_cash_delta: '-91.00',
  amount_range: { min: '-97.00', max: '-83.00' },
  next_due_date: '2026-11-05',
  evidence_count: 3,
  evidence: [
    { date: '2026-09-02', amount: '-91.00' },
    { date: '2026-08-05', amount: '-97.00' },
    { date: '2026-07-03', amount: '-83.00' },
  ],
  explanation: 'Seen 3 times on a monthly pattern.',
  reason_codes: ['3_occurrences', 'cadence_monthly'],
}
const plan = {
  stream_id: 's1',
  account_id: 'sav',
  display_name: 'Rent',
  status: 'confirmed',
  source: 'manual',
  cadence: 'monthly',
  amount_mode: 'fixed',
  amount_cash_delta: '-700.00',
  amount_range: { min: '-700.00', max: '-700.00' },
  next_due_date: '2026-10-21',
  notes: 'Landlord',
}
const ignored = {
  ...plan,
  stream_id: 'i1',
  display_name: 'Gym',
  status: 'ignored',
  source: 'detected',
}

function arrange({ streams = [plan, ignored], candidates = [candidate] } = {}) {
  api.getAccounts.mockResolvedValue({ accounts })
  recurringApi.getRecurringStreams.mockResolvedValue({ streams: [...candidates, ...streams] })
  recurringApi.getRecurringCandidates.mockResolvedValue({ candidates })
}

async function mountSection(props = {}) {
  const wrapper = mount(RecurringTransactionSection, { props })
  await flushPromises()
  return wrapper
}

const button = (wrapper, text) => wrapper.findAll('button').find((b) => b.text() === text)

describe('RecurringTransactionSection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    arrange()
  })

  it('loads all accounts by default instead of a hardcoded account id', async () => {
    await mountSection()
    expect(recurringApi.getRecurringStreams).toHaveBeenCalledWith({
      account_id: undefined,
      page_size: 100,
    })
    expect(recurringApi.getRecurringCandidates).toHaveBeenCalledWith({ account_id: undefined })
  })

  it('shows a loading status, then the three sections', async () => {
    const wrapper = mount(RecurringTransactionSection)
    expect(wrapper.get('[role="status"]').text()).toContain('Loading')
    await flushPromises()
    expect(wrapper.get('[data-testid="needs-review"]').text()).toContain('Needs review (1)')
    expect(wrapper.get('[data-testid="confirmed"]').text()).toContain('Confirmed & upcoming (1)')
    expect(wrapper.get('[data-testid="inactive"]').text()).toContain('Ignored & ended (1)')
    expect(wrapper.find('details').attributes('open')).toBeUndefined() // collapsed by default
  })

  it('renders a candidate with range, cadence, next date, account, evidence and explanation', async () => {
    const wrapper = await mountSection()
    const card = wrapper.get('[data-testid="candidate-c1"]')
    expect(card.text()).toContain('Duke Energy')
    expect(card.text()).toContain('($97.00) to ($83.00)')
    expect(card.text()).toContain('Monthly')
    expect(card.text()).toContain('next 2026-11-05')
    expect(card.text()).toContain('Checking')
    expect(card.text()).toContain('Seen 3 times on a monthly pattern.')
    expect(card.findAll('.evidence li')).toHaveLength(3)
    expect(card.text()).not.toMatch(/tx_|transaction id/i)
    expect(card.findAll('button').map((b) => b.text())).toEqual([
      'Confirm',
      'Edit',
      'Not recurring',
    ])
  })

  it('confirms a suggestion, persists it and reloads', async () => {
    recurringApi.decideRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await wrapper.get('[data-testid="candidate-c1"]').findAll('button')[0].trigger('click')
    await flushPromises()
    expect(recurringApi.decideRecurringStream).toHaveBeenCalledWith('c1', 'confirmed')
    expect(recurringApi.getRecurringStreams).toHaveBeenCalledTimes(2)
  })

  it('dismisses a suggestion with "Not recurring"', async () => {
    recurringApi.decideRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await button(wrapper, 'Not recurring').trigger('click')
    await flushPromises()
    expect(recurringApi.decideRecurringStream).toHaveBeenCalledWith('c1', 'ignored')
  })

  it('keeps the card and explains the failure when a decision cannot be saved', async () => {
    recurringApi.decideRecurringStream.mockRejectedValue({
      response: { data: { message: 'Stream not found' } },
    })
    const wrapper = await mountSection()
    await button(wrapper, 'Confirm').trigger('click')
    await flushPromises()
    expect(wrapper.find('[data-testid="candidate-c1"]').exists()).toBe(true)
    expect(wrapper.get('[role="alert"]').text()).toContain('Stream not found')
  })

  it('adds a manual plan with only account, name, amount and date (no transaction id)', async () => {
    recurringApi.createRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await button(wrapper, '+ Add plan').trigger('click')
    const form = wrapper.get('[data-testid="recurring-form"]')
    expect(form.text()).not.toMatch(/transaction id/i)
    await form.get('[aria-label="Plan account"]').setValue('chk')
    await form.get('[aria-label="Plan name"]').setValue('Duke Energy')
    await form.get('[aria-label="Plan amount in dollars"]').setValue('142.37')
    await form.get('[aria-label="Amount type"]').setValue('variable')
    await form.get('[aria-label="Next due date"]').setValue('2026-11-03')
    await form.trigger('submit')
    await flushPromises()
    expect(recurringApi.createRecurringStream).toHaveBeenCalledWith({
      account_id: 'chk',
      display_name: 'Duke Energy',
      amount_cash_delta: '-142.37',
      amount_mode: 'variable',
      cadence: 'monthly',
      anchor_date: '2026-11-03',
      notes: null,
    })
    expect(wrapper.find('[data-testid="recurring-form"]').exists()).toBe(false)
  })

  it('sends income as a positive cash amount', async () => {
    recurringApi.createRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await button(wrapper, '+ Add plan').trigger('click')
    const form = wrapper.get('[data-testid="recurring-form"]')
    await form.get('[aria-label="Plan account"]').setValue('chk')
    await form.get('[aria-label="Plan name"]').setValue('Paycheck')
    await form.get('[aria-label="Plan amount in dollars"]').setValue('2000')
    await form.get('[aria-label="Money direction"]').setValue('in')
    await form.get('[aria-label="Next due date"]').setValue('2026-11-01')
    await form.trigger('submit')
    await flushPromises()
    expect(recurringApi.createRecurringStream.mock.calls[0][0].amount_cash_delta).toBe('2000.00')
  })

  it('validates the form before calling the API', async () => {
    const wrapper = await mountSection()
    await button(wrapper, '+ Add plan').trigger('click')
    await wrapper.get('[data-testid="recurring-form"]').trigger('submit')
    expect(wrapper.get('.form-error').text()).toContain('Choose an account')
    expect(recurringApi.createRecurringStream).not.toHaveBeenCalled()
  })

  it('edits an existing plan through PATCH with the signed amount', async () => {
    recurringApi.updateRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await wrapper.get('[aria-label="Edit Rent"]').trigger('click')
    const form = wrapper.get('[data-testid="recurring-form"]')
    expect(form.get('[aria-label="Plan amount in dollars"]').element.value).toBe('700.00')
    await form.get('[aria-label="Plan amount in dollars"]').setValue('725')
    await form.trigger('submit')
    await flushPromises()
    expect(recurringApi.updateRecurringStream).toHaveBeenCalledWith(
      's1',
      expect.objectContaining({
        account_id: 'sav',
        amount_cash_delta: '-725.00',
        notes: 'Landlord',
      }),
    )
  })

  it('ends a confirmed plan and can re-confirm an ignored one', async () => {
    recurringApi.decideRecurringStream.mockResolvedValue({})
    const wrapper = await mountSection()
    await wrapper.get('[aria-label="End Rent"]').trigger('click')
    expect(recurringApi.decideRecurringStream).toHaveBeenLastCalledWith('s1', 'ended')
    await flushPromises()
    await wrapper
      .get('[data-testid="inactive"] [aria-label="Confirm Gym as recurring"]')
      .trigger('click')
    expect(recurringApi.decideRecurringStream).toHaveBeenLastCalledWith('i1', 'confirmed')
  })

  it('narrows to one account from the picker', async () => {
    const wrapper = await mountSection()
    await wrapper.get('[data-testid="recurring-account"]').setValue('sav')
    await flushPromises()
    expect(recurringApi.getRecurringStreams).toHaveBeenLastCalledWith({
      account_id: 'sav',
      page_size: 100,
    })
  })

  it('scans, saves proposals and reports the outcome', async () => {
    recurringApi.scanRecurring.mockResolvedValue({
      summary: { created: 2, history_incomplete: true },
    })
    const wrapper = await mountSection()
    await wrapper.get('[data-testid="scan-button"]').trigger('click')
    await flushPromises()
    expect(recurringApi.scanRecurring).toHaveBeenCalledWith({
      account_ids: undefined,
      dry_run: false,
    })
    expect(wrapper.get('[data-testid="scan-summary"]').text()).toContain('2 new suggestions')
    expect(wrapper.get('[data-testid="scan-summary"]').text()).toContain('Only part of the history')
  })

  it('shows empty states and an actionable error', async () => {
    arrange({ streams: [], candidates: [] })
    const empty = await mountSection()
    expect(empty.text()).toContain('Nothing to review')
    expect(empty.text()).toContain('No confirmed plans yet')

    recurringApi.getRecurringStreams.mockRejectedValue({
      response: { data: { code: 'owner_not_configured' } },
    })
    const failed = await mountSection()
    expect(failed.get('[data-testid="recurring-error"]').text()).toContain(
      'not set up on this server',
    )
    expect(button(failed, 'Retry')).toBeTruthy()
  })

  it('pre-fills the form from a transaction through the exposed API', async () => {
    const wrapper = await mountSection()
    wrapper.vm.openFromTransaction({
      transaction_id: 'tx_secret',
      description: 'ACH DEBIT RENT',
      merchant_name: 'Landlord LLC',
      amount: 700,
      provider: 'plaid',
      account_id: 'chk',
    })
    await flushPromises()
    const form = wrapper.get('[data-testid="recurring-form"]')
    expect(form.get('[aria-label="Plan name"]').element.value).toBe('Landlord LLC')
    expect(form.get('[aria-label="Plan amount in dollars"]').element.value).toBe('700.00')
    expect(form.get('[aria-label="Money direction"]').element.value).toBe('out')
    expect(form.get('[aria-label="Plan account"]').element.value).toBe('chk')
    expect(wrapper.html()).not.toContain('tx_secret')

    wrapper.vm.openFromTransaction({ description: 'Refund', amount: -25, provider: 'plaid' })
    await flushPromises()
    expect(wrapper.get('[aria-label="Money direction"]').element.value).toBe('in')
  })

  it('accepts a pre-fetched account list and a fixed account', async () => {
    api.getAccounts.mockClear()
    await mountSection({ accounts, accountId: 'chk' })
    expect(api.getAccounts).not.toHaveBeenCalled()
    expect(recurringApi.getRecurringStreams).toHaveBeenCalledWith({
      account_id: 'chk',
      page_size: 100,
    })
  })

  it('uses non-submitting buttons and labelled controls', async () => {
    const wrapper = await mountSection()
    wrapper.findAll('button').forEach((b) => expect(b.attributes('type')).toBe('button'))
    expect(wrapper.get('section').attributes('aria-labelledby')).toBe('recurring-heading')
  })
})
