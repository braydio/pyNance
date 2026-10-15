// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BillForm from '../BillForm.vue'

const mountForm = () =>
  mount(BillForm, {
    props: {
      visible: true,
      currencyCode: 'USD',
    },
    global: {
      stubs: { UiButton: true },
    },
  })

describe('BillForm', () => {
  it('emits save with normalised payload', async () => {
    const wrapper = mountForm()

    await wrapper.find('#bill-name').setValue('Rent')
    await wrapper.find('#bill-amount').setValue('1200.00')
    await wrapper.find('#bill-due-date').setValue('2024-08-01')
    await wrapper.find('#bill-frequency').setValue('monthly')
    await wrapper.find('#bill-category').setValue('Housing')

    await wrapper.find('form').trigger('submit.prevent')

    const saveEvent = wrapper.emitted('save')?.[0][0]
    expect(saveEvent).toMatchObject({
      name: 'Rent',
      amountCents: 120000,
      frequency: 'monthly',
      category: 'Housing',
    })
  })

  it('prevents submission when validation fails', async () => {
    const wrapper = mountForm()
    await wrapper.find('#bill-name').setValue('')
    await wrapper.find('form').trigger('submit.prevent')

    expect(wrapper.emitted('save')).toBeFalsy()
    expect(wrapper.text()).toContain('Name is required.')
  })
})

describe('BillForm accessibility', () => {
  it('marks required fields and links errors to their inputs', async () => {
    const wrapper = mountForm()
    const name = wrapper.find('#bill-name')
    expect(name.attributes('aria-required')).toBe('true')
    expect(wrapper.text()).toContain('required')

    await name.setValue('')
    await name.trigger('blur')
    expect(name.attributes('aria-invalid')).toBe('true')
    expect(name.attributes('aria-describedby')).toBe('bill-name-error')
    expect(wrapper.find('#bill-name-error').text()).toContain('Name is required')
    expect(wrapper.find('#bill-name-error').attributes('role')).toBe('alert')

    await wrapper.find('#bill-name').setValue('Rent')
    expect(wrapper.find('#bill-name').attributes('aria-invalid')).toBeUndefined()
  })

  it('keeps the amount preview associated with the amount field and explains a disabled save', async () => {
    const wrapper = mountForm()
    const amount = wrapper.find('#bill-amount')
    expect(amount.attributes('aria-describedby')).toContain('bill-amount-preview')
    await amount.setValue('-4')
    await amount.trigger('blur')
    expect(amount.attributes('aria-describedby')).toContain('bill-amount-error')
    const reason = wrapper.find('#bill-disabled-reason')
    expect(reason.exists()).toBe(true)
    expect(reason.text()).toContain('amount')
  })
})
