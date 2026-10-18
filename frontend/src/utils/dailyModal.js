/**
 * Load every transaction for one day (transfers included) in bounded pages.
 *
 * @param {(params: Record<string, unknown>) => Promise<{transactions?: unknown[], total?: number}>} fetcher
 * @param {string} isoDate YYYY-MM-DD
 * @param {{pageSize?: number, maxPages?: number}} [options]
 * @returns {Promise<{rows: unknown[], total: number, partial: boolean}>}
 */
export async function loadDayTransactions(
  fetcher,
  isoDate,
  { pageSize = 1000, maxPages = 5 } = {},
) {
  const rows = []
  let total = 0
  for (let page = 1; page <= maxPages; page += 1) {
    const result = await fetcher({
      start_date: isoDate,
      end_date: isoDate,
      page,
      page_size: pageSize,
      include_transfers: true,
    })
    const batch = result?.transactions || []
    rows.push(...batch)
    total = Number(result?.total ?? rows.length)
    if (!batch.length || rows.length >= total) break
  }
  return { rows, total, partial: rows.length < total }
}
