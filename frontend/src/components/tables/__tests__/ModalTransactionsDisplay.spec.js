// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ModalTransactionsDisplay from '../ModalTransactionsDisplay.vue'

describe('ModalTransactionsDisplay.vue', () => {
  it('renders category display text when category visuals are enabled', () => {
    const wrapper = mount(ModalTransactionsDisplay, {
      props: {
        showCategoryVisuals: true,
        transactions: [
          {
            transaction_id: 'tx-1',
            account_name: 'Checking',
            institution_name: 'Bank',
            merchant_name: 'Local Store',
            description: 'Card purchase',
            amount: -42.33,
            category_icon_url: 'https://example.com/icon.svg',
            category_display: 'Food and Drink: Restaurants',
            date: '2026-02-01',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('Food and Drink: Restaurants')
  })

  it('joins category array values when display name fields are unavailable', () => {
    const wrapper = mount(ModalTransactionsDisplay, {
      props: {
        showCategoryVisuals: true,
        transactions: [
          {
            transaction_id: 'tx-2',
            account_name: 'Checking',
            institution_name: 'Bank',
            merchant_name: 'Pharmacy',
            description: 'OTC meds',
            amount: -10,
            category: ['Health', 'Pharmacy'],
            date: '2026-02-01',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('Health: Pharmacy')
  })
})

describe('ModalTransactionsDisplay flow styling', () => {
  const base = { account_name: 'Checking', institution_name: 'Bank', date: '2026-10-13' }
  it('keeps transfers neutral and labelled while income stays green', () => {
    const wrapper = mount(ModalTransactionsDisplay, {
      props: {
        transactions: [
          {
            ...base,
            transaction_id: 'z',
            amount: 200,
            reporting_flow_kind: 'transfer',
            flow_reason_codes: ['confirmed_internal'],
          },
          { ...base, transaction_id: 'p', amount: 1000, reporting_flow_kind: 'income' },
          { ...base, transaction_id: 'b', amount: 100, reporting_flow_kind: 'unclassified' },
        ],
      },
    })
    const amounts = wrapper
      .findAll('tbody tr')
      .map((r) => r.findAll('td')[2].find('span').classes())
    expect(amounts[0].join(' ')).toContain('--color-text-light')
    expect(amounts[1].join(' ')).toContain('--color-accent-green')
    expect(amounts[2].join(' ')).toContain('--color-text-light')
    const chips = wrapper.findAll('[data-testid="flow-chip"]')
    expect(chips.map((c) => c.text())).toEqual(['Transfer', 'Review'])
    expect(chips[0].attributes('title')).toContain('Confirmed transfer')
  })

  it('still emits row-click for transfer rows', async () => {
    const wrapper = mount(ModalTransactionsDisplay, {
      props: {
        transactions: [{ transaction_id: 'z', amount: 5, reporting_flow_kind: 'transfer' }],
      },
    })
    await wrapper.find('tbody tr').trigger('click')
    expect(wrapper.emitted('row-click')).toHaveLength(1)
  })

  it('has a caption, column scopes and keyboard-selectable rows that emit row-click', async () => {
    const tx = {
      transaction_id: 'tx-k',
      account_name: 'Checking',
      institution_name: 'Bank',
      merchant_name: 'Cafe',
      amount: -3,
      date: '2026-02-01',
    }
    const wrapper = mount(ModalTransactionsDisplay, { props: { transactions: [tx] } })
    expect(wrapper.find('caption').text()).toContain('1')
    wrapper.findAll('th').forEach((th) => expect(th.attributes('scope')).toBe('col'))
    const row = wrapper.get('tbody tr')
    expect(row.attributes('tabindex')).toBe('0')
    await row.trigger('keydown', { key: 'Enter' })
    await row.trigger('click')
    expect(wrapper.emitted('row-click')).toHaveLength(2)
    expect(wrapper.emitted('row-click')[0][0]).toEqual(tx)
  })
})
