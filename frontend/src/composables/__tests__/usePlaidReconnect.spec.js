import { afterEach, describe, expect, it, vi } from 'vitest'
import api from '@/services/api'
import { usePlaidReconnect } from '@/composables/usePlaidReconnect'
import {
  reconnectConnectionGroups,
  uniqueReconnectConnections,
} from '@/utils/plaidConnectionStatus'

vi.mock('@/services/api', () => ({ default: { generatePlaidUpdateLinkToken: vi.fn() } }))

describe('usePlaidReconnect', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    delete window.Plaid
  })

  it('prefers connection_id and runs the Link success callback', async () => {
    const success = vi.fn()
    const open = vi.fn()
    window.Plaid = {
      create: vi.fn(({ onSuccess }) => ({
        open: () => {
          open()
          onSuccess()
        },
      })),
    }
    api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 'link-token' })
    const result = await usePlaidReconnect().reconnect({
      connectionId: 12,
      accountId: 'acct',
      onSuccess: success,
    })
    expect(result).toEqual({ status: 'verified' })
    expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledWith({ connection_id: 12 })
    expect(open).toHaveBeenCalledOnce()
    expect(success).toHaveBeenCalledOnce()
  })

  it('uses legacy account_id and reports token failure without opening Link', async () => {
    window.Plaid = { create: vi.fn() }
    api.generatePlaidUpdateLinkToken.mockResolvedValue({ message: 'Unavailable' })
    const onError = vi.fn()
    const result = await usePlaidReconnect().reconnect({ accountId: 'acct', onError })
    expect(result).toEqual({ status: 'failed', message: 'Unavailable' })
    expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledWith({ account_id: 'acct' })
    expect(window.Plaid.create).not.toHaveBeenCalled()
    expect(onError).toHaveBeenCalledWith('Unavailable')
  })

  it('deduplicates accounts by connection while keeping separate Items independent', () => {
    const account = (account_id, connection_id) => ({
      account_id,
      connection_status: { provider: 'plaid', state: 'reauth_required', connection_id },
    })
    const connections = uniqueReconnectConnections([
      account('checking', 10),
      account('savings', 10),
      account('credit', 11),
    ])
    expect(connections).toHaveLength(2)
    expect(connections[0].accounts).toHaveLength(2)
    expect(connections[1].connectionId).toBe(11)
  })

  it('keeps legacy reauth accounts reconnectable and independent by account ID', () => {
    const account = (account_id) => ({
      account_id,
      connection_status: { provider: 'plaid', state: 'reauth_required' },
    })
    const connections = uniqueReconnectConnections([account('legacy-a'), account('legacy-b')])
    expect(
      connections.map(({ key, accountId, connectionId }) => ({ key, accountId, connectionId })),
    ).toEqual([
      { key: 'account:legacy-a', accountId: 'legacy-a', connectionId: undefined },
      { key: 'account:legacy-b', accountId: 'legacy-b', connectionId: undefined },
    ])
  })

  it('loads the Plaid script once and forwards Link exit text', async () => {
    vi.spyOn(document, 'querySelector').mockReturnValue(null)
    const append = vi.spyOn(document.head, 'appendChild').mockImplementation((script) => {
      window.Plaid = {
        create: ({ onExit }) => ({ open: () => onExit({ display_message: 'Please try later' }) }),
      }
      script.onload()
      return script
    })
    api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 'link-token' })
    const onError = vi.fn()
    const reconnect = usePlaidReconnect().reconnect
    await reconnect({ accountId: 'a', onError })
    await reconnect({ accountId: 'b', onError })
    expect(append).toHaveBeenCalledOnce()
    expect(onError).toHaveBeenCalledWith('Please try later')
  })

  describe('session lifecycle', () => {
    function deferredLink() {
      const link = { handlers: null, open: vi.fn() }
      window.Plaid = {
        create: vi.fn((handlers) => {
          link.handlers = handlers
          return { open: link.open }
        }),
      }
      return link
    }
    const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

    it('joins repeat clicks for one connection into a single token request and Link window', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const { reconnect } = usePlaidReconnect()
      const first = reconnect({ connectionId: 5 })
      const second = reconnect({ connectionId: 5 })
      expect(second).toBe(first)
      await flush()
      expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledTimes(1)
      expect(window.Plaid.create).toHaveBeenCalledTimes(1)
      expect(link.open).toHaveBeenCalledTimes(1)
      link.handlers.onSuccess()
      expect(await first).toEqual({ status: 'verified' })
    })

    it('reports busy for a different connection while Link is open, then allows retry', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const { reconnect, activeKey } = usePlaidReconnect()
      const first = reconnect({ connectionId: 1 })
      expect(activeKey.value).toBe('connection:1')
      const other = await reconnect({ connectionId: 2 })
      expect(other.status).toBe('busy')
      expect(other.activeKey).toBe('connection:1')
      expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledTimes(1)
      await flush()
      link.handlers.onExit(null)
      await first
      expect(activeKey.value).toBeNull()
      const retry = reconnect({ connectionId: 2 })
      await flush()
      link.handlers.onSuccess()
      expect((await retry).status).toBe('verified')
    })

    it('does not complete when Link merely opens', async () => {
      deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const { reconnect, activeKey } = usePlaidReconnect()
      let done = false
      const pending = reconnect({ connectionId: 3 }).then((r) => {
        done = true
        return r
      })
      await flush()
      expect(done).toBe(false)
      expect(activeKey.value).toBe('connection:3')
      window.Plaid.create.mock.calls[0][0].onExit(null)
      expect(await pending).toEqual({ status: 'cancelled' })
    })

    it('settles clean exit as cancelled without calling onError or onSuccess', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const onError = vi.fn()
      const onSuccess = vi.fn()
      const result = usePlaidReconnect().reconnect({ connectionId: 4, onError, onSuccess })
      await flush()
      link.handlers.onExit(undefined)
      expect(await result).toEqual({ status: 'cancelled' })
      expect(onError).not.toHaveBeenCalled()
      expect(onSuccess).not.toHaveBeenCalled()
    })

    it('settles error exit as failed with the Plaid message and releases the lock', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const onError = vi.fn()
      const { reconnect, activeKey } = usePlaidReconnect()
      const result = reconnect({ connectionId: 6, onError })
      await flush()
      link.handlers.onExit({ display_message: 'Bank is down' })
      expect(await result).toEqual({ status: 'failed', message: 'Bank is down' })
      expect(onError).toHaveBeenCalledWith('Bank is down')
      expect(activeKey.value).toBeNull()
    })

    it('ignores a late onExit after a successful verification', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const onError = vi.fn()
      const result = usePlaidReconnect().reconnect({
        connectionId: 7,
        onError,
        onSuccess: async () => {},
      })
      await flush()
      await link.handlers.onSuccess()
      link.handlers.onExit({ display_message: 'late' })
      expect(await result).toEqual({ status: 'verified' })
      expect(onError).not.toHaveBeenCalled()
    })

    it('turns a rejected verification into a failed result and does not leak the lock', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const { reconnect, activeKey } = usePlaidReconnect()
      const result = reconnect({
        connectionId: 8,
        onSuccess: async () => {
          throw new Error('Refresh failed')
        },
      })
      await flush()
      link.handlers.onSuccess()
      expect(await result).toEqual({ status: 'failed', message: 'Refresh failed' })
      expect(activeKey.value).toBeNull()
    })

    it('recovers from a token failure and succeeds on retry', async () => {
      const link = deferredLink()
      api.generatePlaidUpdateLinkToken.mockRejectedValueOnce(new Error('network'))
      const { reconnect } = usePlaidReconnect()
      expect(await reconnect({ connectionId: 9 })).toEqual({ status: 'failed', message: 'network' })
      api.generatePlaidUpdateLinkToken.mockResolvedValue({ link_token: 't' })
      const retry = reconnect({ connectionId: 9 })
      await flush()
      link.handlers.onSuccess()
      expect((await retry).status).toBe('verified')
    })
  })

  describe('reconnectConnectionGroups', () => {
    const acct = (account_id, connection_id, state = 'reauth_required') => ({
      account_id,
      connection_status: { provider: 'plaid', state, connection_id },
    })

    it('shows one group for a three-account Item even with different error messages', () => {
      const accounts = [acct('a', 10), acct('b', 10), acct('c', 10)]
      const errors = [
        { account_ids: ['a'], plaid_error_code: 'ITEM_LOGIN_REQUIRED', plaid_error_message: 'one' },
        { account_ids: ['b'], plaid_error_code: 'ITEM_LOGIN_REQUIRED', plaid_error_message: 'two' },
        {
          account_ids: ['c'],
          plaid_error_code: 'ITEM_LOGIN_REQUIRED',
          plaid_error_message: 'three',
        },
      ]
      const groups = reconnectConnectionGroups(accounts, errors)
      expect(groups).toHaveLength(1)
      expect(groups[0].accountIds).toEqual(['a', 'b', 'c'])
      expect(groups[0].errors).toEqual(['one', 'two', 'three'])
    })

    it('keeps two Items at the same institution as two groups', () => {
      const groups = reconnectConnectionGroups([acct('a', 1), acct('b', 2)])
      expect(groups.map((g) => g.key)).toEqual(['connection:1', 'connection:2'])
    })

    it('does not let a stale refresh error override a healthy persisted Item', () => {
      const groups = reconnectConnectionGroups(
        [acct('a', 1, 'healthy')],
        [{ account_ids: ['a'], plaid_error_code: 'ITEM_LOGIN_REQUIRED', connection_id: 1 }],
      )
      expect(groups).toEqual([])
    })

    it('uses a refresh error for accounts with no persisted status, without merging by institution', () => {
      const groups = reconnectConnectionGroups(
        [
          { account_id: 'x', institution_name: 'Bank' },
          { account_id: 'y', institution_name: 'Bank' },
        ],
        [{ account_ids: ['x', 'y'], plaid_error_code: 'ITEM_LOGIN_REQUIRED' }],
      )
      expect(groups.map((g) => g.key)).toEqual(['account:x', 'account:y'])
    })

    it('is stable across repeated calls', () => {
      const accounts = [acct('a', 10), acct('b', 10)]
      expect(reconnectConnectionGroups(accounts)).toEqual(reconnectConnectionGroups(accounts))
      expect(reconnectConnectionGroups(accounts)).toHaveLength(1)
    })
  })
})
