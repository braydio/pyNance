// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import LinkedAccountsSection from '../LinkedAccountsSection.vue'

function mountComponent() {
  return mount(LinkedAccountsSection, {
    global: {
      stubs: {
        Card: { template: '<div><slot /></div>' },
        UiButton: { template: '<button><slot /></button>' },
      },
    },
  })
}

describe('LinkedAccountsSection', () => {
  it('renders default grouped accounts with promotions', () => {
    const wrapper = mountComponent()

    expect(wrapper.find('[data-testid="linked-accounts-section"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="account-type-Credit Card"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="institution-American Express"]').exists()).toBe(true)

    const cardSummary = wrapper.find('[data-testid="account-amex-blue-cash"]').text()
    expect(cardSummary).toContain('26.99%')
    expect(wrapper.find('[data-testid="promo-list-amex-blue-cash"]').text()).toContain('Groceries')
  })

  it('allows adding a custom promotion entry', async () => {
    const wrapper = mountComponent()

    await wrapper.find('[data-testid="promo-category-amex-blue-cash"]').setValue('custom')
    await wrapper.find('[data-testid="promo-custom-category-amex-blue-cash"]').setValue('Dining Out')
    await wrapper.find('[data-testid="promo-rate-amex-blue-cash"]').setValue('4.5')

    await wrapper.find('[data-testid="promo-form-amex-blue-cash"]').trigger('submit.prevent')
    await nextTick()

    const promoListText = wrapper.find('[data-testid="promo-list-amex-blue-cash"]').text()
    expect(promoListText).toContain('Dining Out')
    expect(promoListText).toContain('4.50%')
  })
})
