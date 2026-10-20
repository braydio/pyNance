/**
 * Summaries over transaction rows that carry the backend's economic-flow classification.
 *
 * The backend (`transaction_flow_classification`) decides each row's `reporting_flow_kind` and
 * `economic_amount`; nothing here guesses a classification from a sign, a category or a name.
 */

const CENT = 100

/** Round a money sum to cents so repeated float addition never shows 0.30000000000000004. */
function money(value) {
  return Math.round(value * CENT) / CENT
}

const KIND_LABELS = {
  income: 'Income',
  expense: 'Expense',
  refund: 'Refund',
  transfer: 'Transfer',
  debt_settlement: 'Debt payment',
  investment_movement: 'Investment',
  unclassified: 'Review',
}

const REASON_LABELS = {
  confirmed_internal: 'Confirmed transfer between your accounts',
  pfc_account_transfer_unpaired: 'Looks like a transfer, but no matching pair was found',
}

/**
 * @param {Record<string, unknown>} tx
 * @returns {boolean} Whether the row carries a backend classification.
 */
export function hasFlowKind(tx) {
  return typeof tx?.reporting_flow_kind === 'string' && tx.reporting_flow_kind !== ''
}

/**
 * Short chip text for a row, or '' for ordinary income/expense/refund rows and unclassified feeds.
 *
 * @param {Record<string, unknown>} tx
 */
export function flowChipLabel(tx) {
  if (!hasFlowKind(tx)) return ''
  const kind = tx.reporting_flow_kind
  return kind === 'income' || kind === 'expense' || kind === 'refund'
    ? ''
    : KIND_LABELS[kind] || 'Review'
}

/**
 * Tooltip text explaining why the backend classified a row the way it did.
 *
 * @param {Record<string, unknown>} tx
 */
export function flowTitle(tx) {
  if (!hasFlowKind(tx)) return ''
  const reasons = Array.isArray(tx.flow_reason_codes) ? tx.flow_reason_codes : []
  const text = reasons.map((code) => REASON_LABELS[code] || String(code).replace(/_/g, ' '))
  const confidence = tx.flow_confidence ? ` (${tx.flow_confidence} confidence)` : ''
  return `${KIND_LABELS[tx.reporting_flow_kind] || 'Review'}${confidence}${text.length ? `: ${text.join('; ')}` : ''}`
}

/**
 * Aggregate rows into economic totals and separately-labelled cash movement.
 *
 * When no row carries a classification (a feed that predates it) `classified` is false and callers
 * should fall back to their legacy summary.
 *
 * @param {Array<Record<string, unknown>>} rows
 */
export function summarizeFlows(rows) {
  const list = Array.isArray(rows) ? rows : []
  const out = {
    classified: list.some(hasFlowKind),
    income: 0,
    expense: 0,
    refunds: 0,
    net: 0,
    transfersIn: 0,
    transfersOut: 0,
    transferCount: 0,
    debtPayments: 0,
    debtCount: 0,
    investment: 0,
    investmentCount: 0,
    unclassifiedCount: 0,
    unclassifiedAmount: 0,
    pendingCount: 0,
    counted: 0,
  }
  for (const tx of list) {
    if (tx?.pending) {
      out.pendingCount += 1
      continue
    }
    out.counted += 1
    const kind = hasFlowKind(tx) ? tx.reporting_flow_kind : 'unclassified'
    const delta = Number(tx?.signed_account_delta ?? tx?.amount) || 0
    const economic = Number(tx?.economic_amount)
    if (kind === 'income') out.income += Number.isFinite(economic) ? economic : 0
    else if (kind === 'expense') out.expense += Number.isFinite(economic) ? economic : 0
    else if (kind === 'refund') out.refunds += Number.isFinite(economic) ? economic : 0
    else if (kind === 'transfer') {
      out.transferCount += 1
      if (delta > 0) out.transfersIn += delta
      else out.transfersOut += Math.abs(delta)
    } else if (kind === 'debt_settlement') {
      out.debtCount += 1
      out.debtPayments += Math.abs(delta)
    } else if (kind === 'investment_movement') {
      out.investmentCount += 1
      out.investment += Math.abs(delta)
    } else {
      out.unclassifiedCount += 1
      out.unclassifiedAmount += delta
    }
  }
  for (const key of [
    'income',
    'expense',
    'refunds',
    'transfersIn',
    'transfersOut',
    'debtPayments',
    'investment',
    'unclassifiedAmount',
  ]) {
    out[key] = money(out[key])
  }
  out.net = money(out.income + out.expense + out.refunds)
  return out
}

/**
 * Compare modal totals with the chart bucket for the same day.
 *
 * @param {ReturnType<typeof summarizeFlows>} summary
 * @param {{income:number, expenses:number, net:number}|null} reference Chart values for the day.
 * @returns {boolean} True when there is a reference and it disagrees by at least a cent.
 */
export function disagreesWithChart(summary, reference) {
  if (!reference || !summary.classified) return false
  const close = (a, b) => Math.abs(Number(a) - Number(b)) < 0.005
  return !(
    close(summary.income, reference.income) &&
    close(summary.expense, reference.expenses) &&
    close(summary.net, reference.net)
  )
}

/**
 * Subtotal of the rows actually rendered on the current page.
 *
 * `cashMovement` is the signed sum of the displayed `amount` values (money out is negative); it is
 * cash movement for those rows, never an income or net figure. `economic` sums only rows the
 * backend classified (`economic_amount`), so transfers and unclassified rows contribute nothing.
 * Placeholder rows and rows without a numeric amount are ignored rather than counted as zero.
 *
 * @param {Array<Record<string, unknown>>} rows
 * @returns {{count: number, cashMovement: number, economic: number}}
 */
export function visiblePageSubtotal(rows) {
  let count = 0
  let cash = 0
  let economic = 0
  for (const row of Array.isArray(rows) ? rows : []) {
    if (!row || row._placeholder) continue
    count += 1
    const amount = Number(row.amount)
    if (row.amount != null && Number.isFinite(amount)) cash += amount
    const economicAmount = Number(row.economic_amount)
    if (row.economic_amount != null && Number.isFinite(economicAmount)) economic += economicAmount
  }
  return { count, cashMovement: money(cash), economic: money(economic) }
}
