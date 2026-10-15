// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AccountPortfolioOverview from '../AccountPortfolioOverview.vue'
import AccountPortfolioList from '../AccountPortfolioList.vue'

const accounts = [
  {
    account_id: 'chk',
    name: 'Checking',
    type: 'depository',
    balance: 1000,
    mask: '1234',
    institution_name: 'Bank A',
    last_refreshed: '2026-10-10T10:00:00Z',
  },
  {
    account_id: 'sav',
    name: 'Savings',
    type: 'depository',
    balance: 0,
    institution_name: 'Bank A',
  },
  {
    account_id: 'cc',
    name: 'Travel Card',
    type: 'credit',
    balance: -250,
    credit_limit: 1000,
    apr: 24.99,
    apr_source: 'provider',
    available_balance: 700,
    institution_name: 'Bank B',
  },
  {
    account_id: 'cc2',
    name: 'No Limit Card',
    type: 'credit',
    balance: -100,
    apr: 29.9,
    institution_name: 'Bank B',
    connection_status: { requires_reauth: true },
  },
  {
    account_id: 'loan',
    name: 'Car Loan',
    type: 'loan',
    balance: -9000,
    institution_name: 'Bank C',
  },
  {
    account_id: 'inv',
    name: 'Brokerage',
    type: 'brokerage',
    is_investment: true,
    balance: 5000,
    institution_name: 'Broker',
  },
  {
    account_id: 'hid',
    name: 'Old Card',
    type: 'credit',
    balance: -50,
    is_hidden: true,
    institution_name: 'Bank B',
  },
]

const filters = (over = {}) => ({
  query: '',
  group: 'all',
  institution: 'all',
  connection: 'all',
  sort: 'name',
  includeHidden: false,
  ...over,
})

describe('AccountPortfolioOverview', () => {
  it('shows assets, liabilities, net and utilization coverage without hidden accounts', () => {
    const wrapper = mount(AccountPortfolioOverview, { props: { accounts } })
    expect(wrapper.get('[data-testid="kpi-assets"]').text()).toContain('$6,000.00')
    expect(wrapper.get('[data-testid="kpi-liabilities"]').text()).toContain('$9,350.00')
    expect(wrapper.get('[data-testid="kpi-net"]').text()).toContain('($3,350.00)')
    expect(wrapper.get('[data-testid="kpi-utilization"]').text()).toContain('25%')
    expect(wrapper.get('[data-testid="utilization-coverage"]').text()).toBe(
      '1 of 2 credit lines have known limits',
    )
    expect(wrapper.find('[data-testid="hidden-excluded-note"]').exists()).toBe(true)
  })

  it('labels totals when hidden accounts are included', () => {
    const wrapper = mount(AccountPortfolioOverview, { props: { accounts, includeHidden: true } })
    expect(wrapper.get('[data-testid="kpi-liabilities"]').text()).toContain('$9,400.00')
    expect(wrapper.find('[data-testid="hidden-included-note"]').exists()).toBe(true)
  })

  it('renders type chips with counts and aggregates, and emits the chosen group', async () => {
    const wrapper = mount(AccountPortfolioOverview, { props: { accounts, group: 'credit' } })
    const credit = wrapper.get('[data-testid="type-chip-credit"]')
    expect(credit.text()).toContain('Credit Cards')
    expect(credit.text()).toContain('2')
    expect(credit.text()).toContain('$350.00 owed')
    expect(credit.attributes('aria-pressed')).toBe('true')
    expect(wrapper.get('[data-testid="type-chip-depository"]').attributes('aria-pressed')).toBe(
      'false',
    )
    await wrapper.get('[data-testid="type-chip-investment"]').trigger('click')
    expect(wrapper.emitted('update:group')[0]).toEqual(['investment'])
  })

  it('does not combine mixed currencies and shows N/A utilization without cards', () => {
    const mixed = mount(AccountPortfolioOverview, {
      props: {
        accounts: [
          { ...accounts[0], currency_code: 'USD' },
          { ...accounts[1], currency_code: 'EUR' },
        ],
      },
    })
    expect(mixed.get('[data-testid="mixed-currency-note"]').exists()).toBe(true)
    expect(mixed.get('[data-testid="kpi-assets"]').text()).toContain('Unavailable')
    expect(mixed.get('[data-testid="kpi-utilization"]').text()).toContain('N/A')
    expect(mixed.get('[data-testid="utilization-coverage"]').text()).toBe('No credit cards')
  })
})

describe('AccountPortfolioList', () => {
  const mountList = (props = {}) =>
    mount(AccountPortfolioList, { props: { accounts, filters: filters(), ...props } })

  it('groups by type then institution and shows shown/total', () => {
    const wrapper = mountList()
    expect(wrapper.get('[data-testid="portfolio-shown-count"]').text()).toContain(
      'Showing 6 of 6 accounts',
    )
    const order = ['depository', 'credit', 'loan', 'investment'].map((g) =>
      wrapper.html().indexOf(`ledger-group-${g}`),
    )
    expect(order.every((i) => i >= 0)).toBe(true)
    expect([...order].sort((a, b) => a - b)).toEqual(order)
  })

  it('shows owed, utilization, available credit, APR provenance and unknown limits truthfully', () => {
    const wrapper = mountList()
    const card = wrapper.get('[data-testid="portfolio-row-cc"]')
    expect(card.get('[data-testid="row-owed"]').text()).toBe('$250.00')
    expect(card.get('[data-testid="row-credit"]').text()).toContain('25% of $1,000.00')
    expect(card.get('[data-testid="row-credit"]').text()).toContain('$700.00 available')
    expect(card.get('[data-testid="row-apr"]').text()).toContain('24.99%')
    expect(card.get('[data-testid="row-apr"]').text()).toContain('Provider-reported')

    const noLimit = wrapper.get('[data-testid="portfolio-row-cc2"]')
    expect(noLimit.get('[data-testid="row-credit"]').text()).toContain('Credit limit unknown')
    expect(noLimit.get('[data-testid="row-apr"]').text()).toContain('Unverified')
    expect(noLimit.text()).toContain('Needs reconnect')

    const checking = wrapper.get('[data-testid="portfolio-row-chk"]')
    expect(checking.find('[data-testid="row-credit"]').exists()).toBe(false)
    expect(checking.get('[data-testid="row-apr"]').text()).toBe('')
    expect(checking.text()).toContain('•••• 1234')
    expect(
      wrapper.get('[data-testid="portfolio-row-sav"] [data-testid="row-balance"]').text(),
    ).toBe('$0.00')
  })

  it('applies the group filter, shows active chips and emits reset/clear', async () => {
    const wrapper = mountList({ filters: filters({ group: 'credit', query: 'travel' }) })
    expect(wrapper.get('[data-testid="portfolio-shown-count"]').text()).toContain('Showing 1 of 6')
    const chips = wrapper.findAll('.portfolio-active__chip')
    expect(chips.map((c) => c.text())).toEqual([
      expect.stringContaining('Credit Cards'),
      expect.stringContaining('travel'),
    ])
    await chips[0].trigger('click')
    expect(wrapper.emitted('update:filters')[0][0]).toMatchObject({ group: 'all', query: 'travel' })
    await wrapper.get('[data-testid="portfolio-reset"]').trigger('click')
    expect(wrapper.emitted('reset')).toHaveLength(1)
  })

  it('emits filter changes from the controls and selection from View details', async () => {
    const wrapper = mountList()
    await wrapper.get('[data-testid="portfolio-search"]').setValue('1234')
    expect(wrapper.emitted('update:filters').at(-1)[0].query).toBe('1234')
    await wrapper.get('[data-testid="portfolio-include-hidden"]').setValue(true)
    expect(wrapper.emitted('update:filters').at(-1)[0].includeHidden).toBe(true)
    await wrapper.get('[data-testid="view-details-cc"]').trigger('click')
    expect(wrapper.emitted('select')[0]).toEqual(['cc'])
  })

  it('explains empty and no-match states and exposes no destructive controls', () => {
    expect(mountList({ accounts: [] }).get('[data-testid="portfolio-empty"]').text()).toContain(
      'No accounts linked',
    )
    const none = mountList({ filters: filters({ query: 'zzz' }) })
    expect(none.get('[data-testid="portfolio-no-match"]').exists()).toBe(true)
    expect(mountList().html()).not.toMatch(/Delete|Hide account/i)
  })

  it('sorts by debt owed with unknown values last', () => {
    const wrapper = mountList({ filters: filters({ sort: 'owed', group: 'credit' }) })
    const ids = wrapper
      .findAll('[data-testid^="portfolio-row-"]')
      .map((r) => r.attributes('data-testid'))
    expect(ids).toEqual(['portfolio-row-cc', 'portfolio-row-cc2'])
  })
})
