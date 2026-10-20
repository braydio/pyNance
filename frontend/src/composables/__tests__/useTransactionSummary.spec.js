// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { ref, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { useTransactionSummary } from '../useTransactionSummary.js'

function setup(filters, fetcher, enabled = ref(true)) {
  let composable
  mount({
    template: '<div />',
    setup() {
      composable = useTransactionSummary(filters, enabled, { fetcher })
      return {}
    },
  })
  return composable
}

const summary = (net) => ({ scope: 'all_matching', economic_net: net, matching_count: 51 })

describe('useTransactionSummary', () => {
  it('requests totals once for the filter set and ignores page and sort changes', async () => {
    const filters = ref({ tx_type: 'debit', page: 1, sort: 'date_desc' })
    const fetcher = vi.fn().mockResolvedValue(summary(725))
    const state = setup(filters, fetcher)
    await flushPromises()
    expect(fetcher).toHaveBeenCalledTimes(1)
    expect(state.matchingSummary.value.economic_net).toBe(725)

    filters.value = { tx_type: 'debit', page: 4, sort: 'amount_desc' }
    await flushPromises()
    expect(fetcher).toHaveBeenCalledTimes(1)

    filters.value = { tx_type: 'debit', search: 'cafe' }
    await flushPromises()
    expect(fetcher).toHaveBeenCalledTimes(2)
  })

  it('never lets a slow response for older filters overwrite the current ones', async () => {
    const filters = ref({ search: 'a' })
    let releaseOld
    const fetcher = vi.fn((params) =>
      params.search === 'a'
        ? new Promise((resolve) => {
            releaseOld = () => resolve(summary(1))
          })
        : Promise.resolve(summary(2)),
    )
    const state = setup(filters, fetcher)
    await nextTick()
    filters.value = { search: 'ab' }
    await flushPromises()
    releaseOld()
    await flushPromises()
    expect(state.matchingSummary.value.economic_net).toBe(2)
    expect(state.status.value).toBe('ready')
  })

  it('flags the last values stale when a refresh for the same filters fails', async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(summary(10))
      .mockRejectedValueOnce(new Error('down'))
    const state = setup(ref({ tx_type: 'debit' }), fetcher)
    await flushPromises()
    await state.refresh()
    expect(state.status.value).toBe('error')
    expect(state.stale.value).toBe(true)
    expect(state.matchingSummary.value.economic_net).toBe(10)
  })

  it('drops old values instead of showing zeros when new filters fail', async () => {
    const filters = ref({ tx_type: 'debit' })
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(summary(10))
      .mockRejectedValueOnce(new Error('down'))
    const state = setup(filters, fetcher)
    await flushPromises()
    filters.value = { tx_type: 'credit' }
    await flushPromises()
    expect(state.matchingSummary.value).toBeNull()
    expect(state.status.value).toBe('error')
    expect(state.stale.value).toBe(false)
  })

  it('does not call the server while disabled', async () => {
    const fetcher = vi.fn().mockResolvedValue(summary(1))
    const enabled = ref(false)
    setup(ref({}), fetcher, enabled)
    await flushPromises()
    expect(fetcher).not.toHaveBeenCalled()
    enabled.value = true
    await flushPromises()
    expect(fetcher).toHaveBeenCalledTimes(1)
  })
})
