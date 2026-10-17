import { describe, it, expect } from 'vitest'
import {
  aprInfo,
  classificationConflict,
  classifyAccount,
  creditUtilization,
  filterPortfolioAccounts,
  groupAccountsForLedger,
  portfolioTotals,
  sortPortfolioAccounts,
  accountUtilization,
} from '../accountPortfolio'

const checking = {
  account_id: 'chk',
  name: 'Checking',
  type: 'depository',
  balance: 1000,
  mask: '1234',
  institution_name: 'Bank A',
}
const card = (over = {}) => ({
  account_id: 'cc',
  name: 'Card',
  type: 'credit',
  balance: -250,
  credit_limit: 1000,
  institution_name: 'Bank B',
  ...over,
})

describe('classifyAccount', () => {
  it.each([
    [{ type: 'depository' }, 'depository'],
    [{ type: 'checking' }, 'depository'],
    [{ type: 'credit' }, 'credit'],
    [{ type: 'Credit Card' }, 'credit'],
    [{ type: 'credit_card' }, 'credit'],
    [{ type: 'loan' }, 'loan'],
    [{ type: 'brokerage', is_investment: false }, 'investment'],
    // Explicit type/subtype wins over the legacy is_investment flag.
    [{ type: 'depository', is_investment: true }, 'depository'],
    [{ type: 'investment', subtype: 'Credit card', is_investment: true }, 'credit'],
    [{ type: 'investment', subtype: 'Savings', is_investment: true }, 'depository'],
    [{ type: 'investment', subtype: 'Checking', is_investment: true }, 'depository'],
    [{ type: 'investment', subtype: 'Brokerage', is_investment: true }, 'investment'],
    [{ type: 'investment', subtype: 'Roth', is_investment: true }, 'investment'],
    [{ type: 'investment', subtype: 'Ira', is_investment: true }, 'investment'],
    [{ type: 'investment', subtype: 'cash management' }, 'investment'],
    [{ type: 'depository', subtype: 'Checking', is_investment: false }, 'depository'],
    [{ type: 'credit', subtype: 'Credit card' }, 'credit'],
    [{ type: 'other', subtype: 'Roth IRA' }, 'investment'],
    [{ type: 'other', is_investment: true }, 'investment'],
    [{ type: 'loan', subtype: 'student', is_investment: true }, 'loan'],
    [{ account_type: 'investment' }, 'investment'],
    [{ type: 'weird' }, 'other'],
    [{}, 'other'],
  ])('%j -> %s', (account, expected) => {
    expect(classifyAccount(account)).toBe(expected)
  })
})

describe('classificationConflict', () => {
  it('reports a legacy flag that disagrees with the explicit type, and nothing else', () => {
    expect(
      classificationConflict({ type: 'investment', subtype: 'Credit card', is_investment: true }),
    ).toEqual({ flag: 'is_investment', classified: 'credit', reason: 'explicit_credit' })
    expect(classificationConflict({ type: 'depository', is_investment: true })).toMatchObject({
      classified: 'depository',
    })
    expect(
      classificationConflict({ type: 'investment', subtype: 'Ira', is_investment: true }),
    ).toBe(null)
    expect(classificationConflict({ type: 'credit', is_investment: false })).toBe(null)
    expect(classificationConflict({})).toBe(null)
  })
})

describe('portfolioTotals', () => {
  it('keeps assets and liabilities separate and nets them', () => {
    const totals = portfolioTotals([
      checking,
      card(),
      { type: 'loan', balance: -5000, account_id: 'l' },
    ])
    expect(totals.assets).toBe(1000)
    expect(totals.liabilities).toBe(5250)
    expect(totals.net).toBe(-4250)
    expect(totals.groups.credit).toMatchObject({ count: 1, total: 250 })
  })

  it('treats a card refund as a credit that reduces owed, not as an asset', () => {
    const totals = portfolioTotals([checking, card({ balance: 40 })])
    expect(totals.assets).toBe(1000)
    expect(totals.liabilities).toBe(0)
    expect(totals.net).toBe(1040)
  })

  it('keeps zero balances and counts unknown balances separately', () => {
    const totals = portfolioTotals([
      { ...checking, balance: 0 },
      { account_id: 'u', type: 'depository' },
    ])
    expect(totals.assets).toBe(0)
    expect(totals.groups.depository).toMatchObject({ count: 2, unknown: 1 })
  })

  it('excludes hidden accounts unless included', () => {
    const hidden = { ...checking, account_id: 'h', is_hidden: true, balance: 500 }
    expect(portfolioTotals([checking, hidden]).assets).toBe(1000)
    const withHidden = portfolioTotals([checking, hidden], { includeHidden: true })
    expect(withHidden.assets).toBe(1500)
    expect(withHidden.hiddenIncluded).toBe(true)
  })

  it('makes aggregates unavailable for mixed currencies', () => {
    const totals = portfolioTotals([
      { ...checking, currency_code: 'USD' },
      { ...checking, account_id: 'eur', currency_code: 'EUR' },
    ])
    expect(totals.mixedCurrency).toBe(true)
    expect(totals.assets).toBeNull()
    expect(totals.net).toBeNull()
  })
})

describe('credit utilization', () => {
  it('is null for non-cards and for missing or zero limits (never 0)', () => {
    expect(accountUtilization(checking)).toBeNull()
    expect(accountUtilization(card({ credit_limit: null }))).toBeNull()
    expect(accountUtilization(card({ credit_limit: 0 }))).toBeNull()
    expect(accountUtilization({ ...checking, credit_limit: 500 })).toBeNull() // overdraft is not a card line
  })

  it('computes per-card and aggregate utilization with coverage', () => {
    expect(accountUtilization(card())).toEqual({ percent: 25, overlimit: false })
    expect(accountUtilization(card({ balance: -1200 }))).toEqual({ percent: 120, overlimit: true })
    const agg = creditUtilization([
      card(),
      card({ account_id: 'cc2', balance: -250, credit_limit: 1000 }),
      card({ account_id: 'cc3', credit_limit: undefined, limit: undefined }),
    ])
    expect(agg).toMatchObject({ percent: 25, known: 2, total: 3 })
    expect(creditUtilization([card({ credit_limit: null })]).percent).toBeNull()
  })

  it('accepts the limit alias and zero balance', () => {
    expect(accountUtilization(card({ credit_limit: undefined, limit: 500, balance: 0 }))).toEqual({
      percent: 0,
      overlimit: false,
    })
  })
})

describe('filter and sort', () => {
  const accounts = [
    checking,
    card(),
    card({ account_id: 'cc2', name: 'Travel Card', balance: -800, mask: '9876', is_hidden: true }),
    {
      account_id: 'rc',
      name: 'Reconnect',
      type: 'credit',
      balance: -10,
      connection_status: { requires_reauth: true },
    },
  ]

  it('searches names, institutions and mask digits and hides hidden accounts by default', () => {
    expect(filterPortfolioAccounts(accounts, { query: 'check' }).map((a) => a.account_id)).toEqual([
      'chk',
    ])
    expect(
      filterPortfolioAccounts(accounts, { query: '•••• 1234' }).map((a) => a.account_id),
    ).toEqual(['chk'])
    expect(filterPortfolioAccounts(accounts, { query: 'bank b' }).map((a) => a.account_id)).toEqual(
      ['cc'],
    )
    expect(filterPortfolioAccounts(accounts, { query: '9876' })).toEqual([])
    expect(filterPortfolioAccounts(accounts, { query: '9876', includeHidden: true })).toHaveLength(
      1,
    )
  })

  it('filters by group, institution and connection state', () => {
    expect(filterPortfolioAccounts(accounts, { group: 'credit' }).map((a) => a.account_id)).toEqual(
      ['cc', 'rc'],
    )
    expect(filterPortfolioAccounts(accounts, { institution: 'Bank A' })).toHaveLength(1)
    expect(
      filterPortfolioAccounts(accounts, { connection: 'needs_reconnect' }).map((a) => a.account_id),
    ).toEqual(['rc'])
  })

  it('sorts unknown values last in both modes', () => {
    const rows = filterPortfolioAccounts(accounts, { includeHidden: true })
    expect(sortPortfolioAccounts(rows, 'utilization').map((a) => a.account_id)).toEqual(
      ['cc2', 'cc', 'chk', 'rc'].filter((id) => rows.some((r) => r.account_id === id)),
    )
    expect(
      sortPortfolioAccounts(rows, 'owed')
        .map((a) => a.account_id)
        .slice(0, 2),
    ).toEqual(['cc2', 'cc'])
    expect(sortPortfolioAccounts(rows, 'name')[0].name).toBe('Card')
  })

  it('sorts APR by reported rates only', () => {
    const rows = [
      card({ account_id: 'a', apr: 20, apr_source: 'provider' }),
      card({ account_id: 'b', apr: 28, apr_source: 'legacy_unverified' }),
      card({ account_id: 'c', apr: 10, apr_source: 'manual' }),
    ]
    expect(sortPortfolioAccounts(rows, 'apr').map((a) => a.account_id)).toEqual(['a', 'c', 'b'])
  })
})

describe('aprInfo', () => {
  it('labels provenance and hides APR on non-liabilities', () => {
    expect(aprInfo(checking).applicable).toBe(false)
    expect(aprInfo(card({ apr: 0, apr_source: null }))).toMatchObject({
      source: 'unverified',
      label: 'Unverified',
    })
    expect(aprInfo(card({ apr: 24.99, apr_source: 'provider' }))).toMatchObject({
      value: 24.99,
      label: 'Provider-reported',
    })
    expect(aprInfo(card({ apr: 12, apr_source: 'manual' })).label).toBe('Entered manually')
    expect(aprInfo(card({ apr: null, estimated_rate: { estimated_rate: 22.1 } }))).toMatchObject({
      source: 'estimated',
      value: 22.1,
    })
    expect(aprInfo(card())).toMatchObject({ source: 'unknown', value: null })
  })
})

describe('groupAccountsForLedger', () => {
  it('groups by type then institution and omits empty groups', () => {
    const grouped = groupAccountsForLedger([
      checking,
      card(),
      card({ account_id: 'cc2', institution_name: 'Bank B' }),
    ])
    expect(grouped.map((g) => g.group)).toEqual(['depository', 'credit'])
    expect(grouped[1].institutions[0]).toMatchObject({ name: 'Bank B' })
    expect(grouped[1].institutions[0].accounts).toHaveLength(2)
  })
})
