import { afterEach, describe, expect, it, vi } from 'vitest'
import api from '@/services/api'
import { usePlaidReconnect } from '@/composables/usePlaidReconnect'

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
})
