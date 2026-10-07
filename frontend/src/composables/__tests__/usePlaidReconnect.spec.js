import { afterEach, describe, expect, it, vi } from 'vitest'
import api from '@/services/api'
import { usePlaidReconnect } from '@/composables/usePlaidReconnect'
import { uniqueReconnectConnections } from '@/utils/plaidConnectionStatus'

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
    await usePlaidReconnect().reconnect({ connectionId: 12, accountId: 'acct', onSuccess: success })
    expect(api.generatePlaidUpdateLinkToken).toHaveBeenCalledWith({ connection_id: 12 })
    expect(open).toHaveBeenCalledOnce()
    expect(success).toHaveBeenCalledOnce()
  })

  it('uses legacy account_id and reports token failure without opening Link', async () => {
    window.Plaid = { create: vi.fn() }
    api.generatePlaidUpdateLinkToken.mockResolvedValue({ message: 'Unavailable' })
    const onError = vi.fn()
    await expect(usePlaidReconnect().reconnect({ accountId: 'acct', onError })).rejects.toThrow(
      'Unavailable',
    )
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
})
