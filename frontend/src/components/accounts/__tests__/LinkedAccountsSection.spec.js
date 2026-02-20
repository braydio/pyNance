// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LinkedAccountsSection from '../LinkedAccountsSection.vue'

function mountComponent(props = {}) {
  return mount(LinkedAccountsSection, {
    props,
    global: {
      stubs: {
        Card: { template: '<div><slot /></div>' },
        UiButton: { template: '<button><slot /></button>' },
      },
    },
  })
}

describe('LinkedAccountsSection', () => {
  it('renders an empty state when real data is empty and demo fallback is disabled', () => {
    const wrapper = mountComponent({ accounts: [], useDemoFallback: false })

    expect(wrapper.text()).toContain(
      'No accounts available yet. Link an account to see details below.',
    )
    expect(wrapper.find('[data-testid="account-type-Credit Card"]').exists()).toBe(false)
  })

  it('renders demo grouped accounts when demo fallback is enabled', () => {
    const wrapper = mountComponent({ accounts: [], useDemoFallback: true })

    expect(wrapper.find('[data-testid="linked-accounts-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="account-type-Credit Card"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="institution-American Express"]').exists()).toBe(true)

    const cardSummary = wrapper.find('[data-testid="account-amex-blue-cash"]').text()
    expect(cardSummary).toContain('26.99%')
    expect(wrapper.find('[data-testid="promo-list-amex-blue-cash"]').text()).toContain('Groceries')
  })

  it('keeps promotion editor hidden by default and does not render add form', () => {
    const wrapper = mountComponent({
      accounts: [
        {
          id: 'acct-1',
          name: 'Cash Rewards',
          institution: 'Test Bank',
          type: 'Credit Card',
          promotions: [{ category: 'Groceries', rate: 3 }],
        },
      ],
      useDemoFallback: false,
    })

    expect(wrapper.find('[data-testid="promo-form-acct-1"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="promo-list-acct-1"]').text()).toContain('Groceries')
  })

  it('emits add-promotion and labels editor as local draft when enabled', async () => {
    const wrapper = mountComponent({
      accounts: [
        {
          id: 'acct-1',
          name: 'Cash Rewards',
          institution: 'Test Bank',
          type: 'Credit Card',
          promotions: [],
        },
      ],
      useDemoFallback: false,
      enablePromotionEditor: true,
    })

    expect(wrapper.find('[data-testid="promo-draft-label-acct-1"]').text()).toContain(
      'Local draft only. Promotions are not persisted yet.',
    )

    await wrapper.find('[data-testid="promo-category-acct-1"]').setValue('custom')
    await wrapper.find('[data-testid="promo-custom-category-acct-1"]').setValue('Dining Out')
    await wrapper.find('[data-testid="promo-rate-acct-1"]').setValue('4.5')

    await wrapper.find('[data-testid="promo-form-acct-1"]').trigger('submit.prevent')
    await nextTick()

    const promoListText = wrapper.find('[data-testid="promo-list-acct-1"]').text()
    expect(promoListText).toContain('Dining Out')
    expect(promoListText).toContain('4.50%')

    const emitted = wrapper.emitted('add-promotion')
    expect(emitted).toBeTruthy()
    expect(emitted[0][0]).toEqual({
      accountId: 'acct-1',
      category: 'Dining Out',
      rate: 4.5,
    })
  })
})
