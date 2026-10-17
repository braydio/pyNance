/**
 * Account portfolio helpers: classification, totals, credit utilization, filtering, sorting.
 *
 * Account balances from `/api/accounts/get_accounts` are display-signed: liabilities are
 * negative (amount owed), assets positive. Unknown values stay `null`; they are never 0.
 */

export const GROUPS = ['depository', 'credit', 'loan', 'investment', 'other']

export const GROUP_LABELS = {
  depository: 'Checking & Savings',
  credit: 'Credit Cards',
  loan: 'Loans & Lines',
  investment: 'Investments',
  other: 'Other',
}

const CREDIT_ALIASES = new Set(['credit', 'credit card', 'creditcard'])
const LOAN_ALIASES = new Set([
  'loan',
  'liability',
  'mortgage',
  'student',
  'student loan',
  'auto',
  'line of credit',
  'home equity',
])
// Bank-style subtypes that identify a spendable deposit account even under an investment-typed item.
const BANK_SUBTYPES = new Set(['checking', 'savings', 'depository'])
const DEPOSITORY_ALIASES = new Set([
  'depository',
  'checking',
  'savings',
  'cash',
  'cash management',
  'money market',
  'cd',
])
const INVESTMENT_PATTERN =
  /\b(investment|brokerage|ira|roth|401\(?k\)?|403\(?b\)?|retirement|pension)\b/

function norm(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
}

function num(value) {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/** Lowercase and collapse separators so `credit_card`, `Credit-Card` and `credit card` compare equal. */
function compact(value) {
  return norm(value).replace(/[_-]+/g, ' ').replace(/\s+/g, ' ')
}

function looksInvestment(value) {
  return INVESTMENT_PATTERN.test(compact(value))
}

/**
 * Classify an account and say why. Explicit type/subtype wins over the legacy `is_investment` flag,
 * because a provider can type a whole item as "investment" while each account's subtype says what it
 * really is (for example a Robinhood "Credit card" or "Savings").
 *
 * Precedence: credit, loan, investment subtype, bank-style subtype (checking/savings), investment
 * type, depository, then the `is_investment` flag, then other.
 *
 * @param {object} account Account row from the accounts API.
 * @returns {{ group: 'depository'|'credit'|'loan'|'investment'|'other', reason: string }}
 */
function resolveClassification(account) {
  const type = compact(account?.account_type ?? account?.type)
  const subtype = compact(account?.subtype)
  if ([subtype, type].some((value) => CREDIT_ALIASES.has(value))) {
    return { group: 'credit', reason: 'explicit_credit' }
  }
  if ([subtype, type].some((value) => LOAN_ALIASES.has(value))) {
    return { group: 'loan', reason: 'explicit_loan' }
  }
  if (looksInvestment(subtype)) return { group: 'investment', reason: 'investment_subtype' }
  if (BANK_SUBTYPES.has(subtype)) return { group: 'depository', reason: 'bank_subtype' }
  if (looksInvestment(type)) return { group: 'investment', reason: 'investment_type' }
  if ([type, subtype].some((value) => DEPOSITORY_ALIASES.has(value))) {
    return { group: 'depository', reason: 'depository_type' }
  }
  if (account?.is_investment) return { group: 'investment', reason: 'is_investment_flag' }
  return { group: 'other', reason: 'unrecognized' }
}

/**
 * Classify an account into one of GROUPS (accepts lowercase provider types).
 *
 * @param {object} account Account row from the accounts API.
 * @returns {'depository'|'credit'|'loan'|'investment'|'other'} Portfolio group.
 */
export function classifyAccount(account) {
  return resolveClassification(account).group
}

/**
 * Report when the legacy `is_investment` flag disagrees with the explicit type/subtype, so the
 * ledger can show the right group while diagnostics still record the mismatch.
 *
 * @param {object} account Account row.
 * @returns {{ flag: 'is_investment', classified: string, reason: string } | null} Conflict or null.
 */
export function classificationConflict(account) {
  if (!account?.is_investment) return null
  const { group, reason } = resolveClassification(account)
  if (group === 'investment' || group === 'other') return null
  return { flag: 'is_investment', classified: group, reason }
}

const GROUP_SINGULAR = {
  depository: 'Deposit account',
  credit: 'Credit card',
  loan: 'Loan',
  investment: 'Investment account',
  other: 'Account',
}

/**
 * Human label for an account's type, consistent with its portfolio group: the provider subtype
 * when it fits the group (Checking, Savings, Brokerage, Ira), else the group's singular name.
 *
 * @param {object} account Account row.
 * @returns {string} Label such as `Credit card`, `Savings` or `Roth`.
 */
export function accountTypeLabel(account) {
  const group = classifyAccount(account)
  const subtype = String(account?.subtype ?? '').trim()
  if (!subtype) return GROUP_SINGULAR[group]
  const fits = classifyAccount({ type: account?.type, subtype }) === group
  if (!fits) return GROUP_SINGULAR[group]
  if (group === 'investment' && /^ira$/i.test(subtype)) return 'IRA'
  return subtype.charAt(0).toUpperCase() + subtype.slice(1).toLowerCase()
}

export function isLiabilityGroup(group) {
  return group === 'credit' || group === 'loan'
}

/** Signed display balance (liabilities negative) or null when unknown. */
export function accountBalance(account) {
  return num(account?.current_balance ?? account?.balance)
}

/** Amount owed on a liability (>= 0), or null for non-liabilities / unknown balance. */
export function amountOwed(account) {
  const group = classifyAccount(account)
  const balance = accountBalance(account)
  if (!isLiabilityGroup(group) || balance === null) return null
  return Math.max(-balance, 0)
}

/** Credit balance (refund/overpayment) on a liability, or 0. */
function creditBalance(account) {
  const balance = accountBalance(account)
  return isLiabilityGroup(classifyAccount(account)) && balance !== null ? Math.max(balance, 0) : 0
}

/** Provider credit line for credit cards only (a bank overdraft limit is never a card line). */
export function creditLimit(account) {
  if (classifyAccount(account) !== 'credit') return null
  const limit = num(account?.credit_limit ?? account?.limit)
  return limit !== null && limit > 0 ? limit : null
}

/**
 * Utilization for one card as a percentage, or null when not a card / no known limit.
 *
 * @param {object} account Account row.
 * @returns {{ percent: number, overlimit: boolean } | null} Utilization.
 */
export function accountUtilization(account) {
  const limit = creditLimit(account)
  const owed = amountOwed(account)
  if (limit === null || owed === null) return null
  return { percent: Math.round((owed / limit) * 1000) / 10, overlimit: owed > limit }
}

/**
 * Aggregate credit utilization over cards with known limits.
 *
 * @param {object[]} accounts Accounts to aggregate.
 * @returns {{ percent: number | null, known: number, total: number, owed: number, limit: number }}
 */
export function creditUtilization(accounts = []) {
  const cards = accounts.filter((account) => classifyAccount(account) === 'credit')
  let owed = 0
  let limit = 0
  let known = 0
  cards.forEach((card) => {
    const cardLimit = creditLimit(card)
    const cardOwed = amountOwed(card)
    if (cardLimit === null || cardOwed === null) return
    known += 1
    owed += cardOwed
    limit += cardLimit
  })
  return {
    percent: known ? Math.round((owed / limit) * 1000) / 10 : null,
    known,
    total: cards.length,
    owed,
    limit,
  }
}

function currencyOf(account) {
  const code = String(account?.currency_code ?? '').trim()
  return code ? code.toUpperCase() : null
}

/**
 * Portfolio totals. Hidden accounts are excluded unless `includeHidden`. Mixed currencies
 * make the monetary aggregates unavailable (null) instead of silently adding them.
 *
 * @param {object[]} accounts Accounts.
 * @param {{ includeHidden?: boolean }} [options] Visibility options.
 * @returns {object} Totals with per-group breakdown and coverage.
 */
export function portfolioTotals(accounts = [], { includeHidden = false } = {}) {
  const included = accounts.filter((account) => includeHidden || !account?.is_hidden)
  const currencies = new Set(included.map(currencyOf).filter(Boolean))
  const mixedCurrency = currencies.size > 1
  const groups = Object.fromEntries(
    GROUPS.map((group) => [group, { count: 0, total: 0, unknown: 0 }]),
  )

  let assets = 0
  let liabilities = 0
  let credits = 0
  included.forEach((account) => {
    const group = classifyAccount(account)
    const bucket = groups[group]
    bucket.count += 1
    const balance = accountBalance(account)
    if (balance === null) {
      bucket.unknown += 1
      return
    }
    if (isLiabilityGroup(group)) {
      const owed = Math.max(-balance, 0)
      liabilities += owed
      credits += creditBalance(account)
      bucket.total += owed
    } else if (group === 'other' && balance < 0) {
      liabilities += -balance
      bucket.total += balance
    } else {
      assets += balance
      bucket.total += balance
    }
  })

  const money = (value) => (mixedCurrency ? null : value)
  const unknownBalances = included.filter((account) => accountBalance(account) === null).length
  const hiddenCount = accounts.filter((account) => account?.is_hidden).length
  return {
    accountCount: included.length,
    linkedCount: accounts.length,
    // Totals leave out hidden accounts, so they describe the visible accounts only.
    partial: !includeHidden && hiddenCount > 0,
    unknownBalances,
    classificationConflicts: included.filter((account) => classificationConflict(account)).length,
    hiddenIncluded: includeHidden,
    hiddenCount,
    currency: currencies.size === 1 ? [...currencies][0] : currencies.size ? null : 'USD',
    mixedCurrency,
    assets: money(assets),
    liabilities: money(liabilities),
    // Card refunds/overpayments reduce what is owed overall.
    net: money(assets + credits - liabilities),
    utilization: creditUtilization(included),
    groups,
  }
}

function digits(value) {
  return String(value ?? '').replace(/\D/g, '')
}

function connectionState(account) {
  return account?.connection_status?.requires_reauth ||
    account?.connection_status?.state === 'reauth_required'
    ? 'needs_reconnect'
    : 'ok'
}

/**
 * Filter accounts by text (name/institution/mask digits), group, institution, connection state.
 *
 * @param {object[]} accounts Accounts.
 * @param {object} [filters] `{ query, group, institution, connection, includeHidden }`.
 * @returns {object[]} Matching accounts.
 */
export function filterPortfolioAccounts(accounts = [], filters = {}) {
  const query = norm(filters.query)
  const queryDigits = digits(filters.query)
  return accounts.filter((account) => {
    if (!filters.includeHidden && account?.is_hidden) return false
    if (filters.group && filters.group !== 'all' && classifyAccount(account) !== filters.group) {
      return false
    }
    if (filters.institution && filters.institution !== 'all') {
      if ((account.institution_name || 'Unknown institution') !== filters.institution) return false
    }
    if (filters.connection && filters.connection !== 'all') {
      if (connectionState(account) !== filters.connection) return false
    }
    if (query) {
      const haystack = [account.name, account.display_name, account.institution_name]
        .map(norm)
        .join(' ')
      const matchesText = haystack.includes(query)
      const matchesMask = queryDigits.length >= 2 && digits(account.mask).includes(queryDigits)
      if (!matchesText && !matchesMask) return false
    }
    return true
  })
}

/**
 * Whether an APR value is a reported (provider/manual) rate, an estimate, or unverified.
 *
 * @param {object} account Account row.
 * @returns {{ applicable: boolean, value: number | null, source: string, label: string }}
 */
export function aprInfo(account) {
  const group = classifyAccount(account)
  if (!isLiabilityGroup(group)) {
    return { applicable: false, value: null, source: 'n/a', label: '' }
  }
  const apr = num(account?.apr)
  const source = account?.apr_source || null
  if (apr !== null && (source === 'provider' || source === 'manual')) {
    return {
      applicable: true,
      value: apr,
      source,
      label: source === 'provider' ? 'Provider-reported' : 'Entered manually',
    }
  }
  const estimated = num(account?.estimated_rate?.estimated_rate)
  if (estimated !== null) {
    return { applicable: true, value: estimated, source: 'estimated', label: 'Estimated' }
  }
  if (apr !== null) {
    return { applicable: true, value: apr, source: 'unverified', label: 'Unverified' }
  }
  return { applicable: true, value: null, source: 'unknown', label: 'APR unknown' }
}

function syncedAt(account) {
  const stamp = Date.parse(account?.last_refreshed ?? account?.balance_as_of ?? '')
  return Number.isNaN(stamp) ? null : stamp
}

const NULLS_LAST = (value) => (value === null || value === undefined ? null : value)

export const SORT_OPTIONS = [
  { value: 'name', label: 'Name' },
  { value: 'balance', label: 'Balance (high to low)' },
  { value: 'owed', label: 'Debt owed' },
  { value: 'utilization', label: 'Utilization' },
  { value: 'apr', label: 'APR (known only)' },
  { value: 'synced', label: 'Recently synced' },
]

function sortValue(account, key) {
  switch (key) {
    case 'balance':
      return accountBalance(account)
    case 'owed':
      return amountOwed(account)
    case 'utilization':
      return accountUtilization(account)?.percent ?? null
    case 'apr': {
      const info = aprInfo(account)
      return info.source === 'provider' || info.source === 'manual' ? info.value : null
    }
    case 'synced':
      return syncedAt(account)
    default:
      return norm(account?.display_name || account?.name)
  }
}

/**
 * Sort accounts; unknown values always sort last regardless of direction.
 *
 * @param {object[]} accounts Accounts.
 * @param {string} [key] One of SORT_OPTIONS values.
 * @returns {object[]} New sorted array.
 */
export function sortPortfolioAccounts(accounts = [], key = 'name') {
  const ascending = key === 'name'
  return [...accounts].sort((left, right) => {
    const a = NULLS_LAST(sortValue(left, key))
    const b = NULLS_LAST(sortValue(right, key))
    if (a === null && b === null) return norm(left?.name).localeCompare(norm(right?.name))
    if (a === null) return 1
    if (b === null) return -1
    if (a === b) return norm(left?.name).localeCompare(norm(right?.name))
    if (typeof a === 'string') return ascending ? a.localeCompare(b) : b.localeCompare(a)
    return b - a
  })
}

/**
 * Group sorted accounts by type then institution for the ledger.
 *
 * @param {object[]} accounts Accounts (already filtered/sorted).
 * @returns {Array<{ group: string, label: string, count: number, institutions: Array }>}
 */
export function groupAccountsForLedger(accounts = []) {
  return GROUPS.map((group) => {
    const members = accounts.filter((account) => classifyAccount(account) === group)
    const byInstitution = new Map()
    members.forEach((account) => {
      const name = account.institution_name || 'Unknown institution'
      if (!byInstitution.has(name)) byInstitution.set(name, [])
      byInstitution.get(name).push(account)
    })
    return {
      group,
      label: GROUP_LABELS[group],
      count: members.length,
      institutions: [...byInstitution.entries()]
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([name, rows]) => ({ name, accounts: rows })),
    }
  }).filter((entry) => entry.count > 0)
}

/** Distinct institution names for the filter select. */
export function institutionOptions(accounts = []) {
  return [
    ...new Set(accounts.map((account) => account.institution_name || 'Unknown institution')),
  ].sort((a, b) => a.localeCompare(b))
}

/** Sync status label for a row. */
export function syncStatus(account) {
  if (connectionState(account) === 'needs_reconnect') return 'Needs reconnect'
  const stamp = syncedAt(account)
  if (stamp === null) return 'Not synced yet'
  return `Synced ${new Date(stamp).toLocaleDateString()}`
}

export { connectionState }
