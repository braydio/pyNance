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
