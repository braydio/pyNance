// File: src/composables/useTransactionSummary.js

/**
 * All-matching totals for the Activity table.
 *
 * `matchingSummary` always describes every row that matches the canonical filter set, independent
 * of page and sort. Responses are keyed by the filter hash, so a slow response for an earlier
 * filter can never overwrite the current one. On failure the last values for the *same* filters
 * are kept and flagged `stale`; after a filter change a failure clears them, because values for
 * other filters would be wrong rather than old.
 */
import { ref, computed, watch, onScopeDispose } from 'vue'
import { fetchTransactionsSummary } from '@/api/transactions'

/**
 * @param {import('vue').Ref<Record<string, unknown>>} filtersRef - Canonical filters (page, sort
 *   and balance flags are ignored).
 * @param {import('vue').Ref<boolean>} [enabledRef] - When false nothing is requested.
 * @param {{fetcher?: Function}} [options]
 */
export function useTransactionSummary(filtersRef, enabledRef = ref(true), options = {}) {
  const fetcher = options.fetcher || fetchTransactionsSummary
  const matchingSummary = ref(null)
  const status = ref('idle') // idle | loading | ready | error
  const error = ref(null)
  const stale = ref(false)
  let sequence = 0
  let loadedHash = ''
  let controller = null

  /** Hash of the filters that affect the aggregate (sorting and paging do not). */
  const summaryHash = computed(() => {
    // eslint-disable-next-line no-unused-vars
    const { page, page_size, sort, include_running_balance, transaction_id, ...rest } =
      filtersRef.value || {}
    return JSON.stringify(
      Object.keys(rest)
        .sort()
        .reduce((acc, key) => {
          acc[key] = rest[key]
          return acc
        }, {}),
    )
  })

  async function refresh() {
    if (!enabledRef.value) return
    const requestHash = summaryHash.value
    const requestId = ++sequence
    controller?.abort?.()
    controller = typeof AbortController === 'undefined' ? null : new AbortController()
    status.value = 'loading'
    error.value = null
    try {
      const data = await fetcher(filtersRef.value || {}, { signal: controller?.signal })
      if (requestId !== sequence || requestHash !== summaryHash.value) return
      matchingSummary.value = data
      loadedHash = requestHash
      stale.value = false
      status.value = 'ready'
    } catch (err) {
      if (requestId !== sequence || requestHash !== summaryHash.value) return
      if (err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError') return
      error.value = err instanceof Error ? err : new Error('Unable to load transaction totals')
      status.value = 'error'
      if (loadedHash === requestHash && matchingSummary.value) {
        stale.value = true
      } else {
        matchingSummary.value = null
        stale.value = false
      }
    }
  }

  watch(
    [summaryHash, enabledRef],
    () => {
      if (loadedHash !== summaryHash.value) {
        matchingSummary.value = null
        stale.value = false
      }
      refresh()
    },
    { immediate: true },
  )

  onScopeDispose(() => {
    sequence += 1
    controller?.abort?.()
  })

  return { matchingSummary, status, error, stale, refresh, summaryHash }
}
