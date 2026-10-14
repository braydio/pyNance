// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import api from '@/services/api'
import RefreshPlaidControls from '../widgets/RefreshPlaidControls.vue'

vi.mock('@/services/api', () => ({
  default: {
    getAccounts: vi.fn(),
    refreshAccounts: vi.fn(),
    generatePlaidUpdateLinkToken: vi.fn(),
    fetchAccountTransactions: vi.fn(),
  },
}))

const child = (account_id, connection_id, state = 'reauth_required') => ({
  account_id,
  name: `Account ${account_id}`,
  institution_name: 'Bank',
  connection_status: { provider: 'plaid', state, connection_id },
})

let openLinks = []
function fakeLink() {
  const link = { handlers: null, open: vi.fn() }
  openLinks.push(link)
  window.Plaid = {
    create: vi.fn((handlers) => {
      link.handlers = handlers
      return { open: link.open }
    }),
  }
  return link
}

async function mountControls(accounts) {
  api.getAccounts.mockResolvedValue({ status: 'success', accounts })
  const wrapper = mount(RefreshPlaidControls, {
    global: {
      stubs: { Card: { template: '<div><slot /></div>' } },
      directives: { clickOutside: {} },
    },
  })
  await flushPromises()
  return wrapper
}
const buttons = (wrapper) =>
  wrapper.findAll('button').filter((b) => /Reconnect with Plaid|Opening Plaid/.test(b.text()))

describe('RefreshPlaidControls Item reconnect', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 'tok' })
    api.refreshAccounts.mockResolvedValue({ status: 'success', refreshed_counts: {}, errors: [] })
  })
  afterEach(async () => {
    openLinks.forEach((link) => link.handlers?.onExit(null))
    openLinks = []
    await flushPromises()
    delete window.Plaid
  })

  it('shows one reconnect action per Item even with differing refresh error messages', async () => {
    const wrapper = await mountControls([child('a', 1), child('b', 1), child('c', 1)])
    api.refreshAccounts.mockResolvedValue({
      status: 'success',
      refreshed_counts: { Bank: 3 },
      errors: ['a', 'b', 'c'].map((id, index) => ({
        account_ids: [id],
        connection_id: 1,
        requires_reauth: true,
        plaid_error_code: 'ITEM_LOGIN_REQUIRED',
        plaid_error_message: `message ${index}`,
      })),
    })
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('Sync Account Activity'))
      .trigger('click')
    await flushPromises()
    expect(buttons(wrapper)).toHaveLength(1)
    expect(wrapper.get('[data-testid="reconnect-account-count"]').text()).toContain('3 accounts')
  })

  it('keeps two Items at the same institution separate', async () => {
    const wrapper = await mountControls([child('a', 1), child('b', 2)])
    expect(buttons(wrapper)).toHaveLength(2)
  })

  it('starts one Link session per click and refreshes every account in the Item', async () => {
    const wrapper = await mountControls([child('a', 1), child('b', 1), child('c', 1)])
    const link = fakeLink()
    await buttons(wrapper)[0].trigger('click')
    await buttons(wrapper)[0].trigger('click')
    await flushPromises()
    expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledTimes(1)
    expect(link.open).toHaveBeenCalledTimes(1)
    await link.handlers.onSuccess()
    await flushPromises()
    expect(api.refreshAccounts).toHaveBeenCalledWith(
      expect.objectContaining({ account_ids: ['a', 'b', 'c'] }),
    )
    // Server still reports reauth, so the warning remains with a usable action.
    expect(wrapper.text()).toContain('still reports')
    expect(buttons(wrapper)[0].attributes('disabled')).toBeUndefined()
  })

  it('removes the warning only once persisted health is confirmed', async () => {
    const wrapper = await mountControls([child('a', 1)])
    const link = fakeLink()
    await buttons(wrapper)[0].trigger('click')
    await flushPromises()
    api.getAccounts.mockResolvedValue({ status: 'success', accounts: [child('a', 1, 'healthy')] })
    await link.handlers.onSuccess()
    await flushPromises()
    expect(buttons(wrapper)).toHaveLength(0)
  })

  it('releases the button on cancel and on failed verification', async () => {
    const wrapper = await mountControls([child('a', 1)])
    const link = fakeLink()
    await buttons(wrapper)[0].trigger('click')
    await flushPromises()
    link.handlers.onExit(null)
    await flushPromises()
    expect(buttons(wrapper)[0].text()).toContain('Reconnect with Plaid')
    expect(buttons(wrapper)[0].attributes('disabled')).toBeUndefined()

    const second = fakeLink()
    api.refreshAccounts.mockRejectedValueOnce(new Error('Refresh unavailable'))
    await buttons(wrapper)[0].trigger('click')
    await flushPromises()
    await second.handlers.onSuccess()
    await flushPromises()
    expect(wrapper.text()).toContain('Refresh unavailable')
    expect(buttons(wrapper)[0].attributes('disabled')).toBeUndefined()
  })

  it('does not merge Item-less accounts by institution', async () => {
    const wrapper = await mountControls([
      { account_id: 'x', name: 'X', institution_name: 'Bank' },
      { account_id: 'y', name: 'Y', institution_name: 'Bank' },
    ])
    api.refreshAccounts.mockResolvedValue({
      status: 'success',
      refreshed_counts: { Bank: 2 },
      errors: [
        { account_ids: ['x', 'y'], requires_reauth: true, plaid_error_code: 'ITEM_LOGIN_REQUIRED' },
      ],
    })
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('Sync Account Activity'))
      .trigger('click')
    await flushPromises()
    expect(buttons(wrapper)).toHaveLength(2)
  })
})
