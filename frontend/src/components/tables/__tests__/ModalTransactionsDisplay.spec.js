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
