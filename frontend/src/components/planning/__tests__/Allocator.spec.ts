import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import Allocator from '../Allocator.vue'

describe('Allocator', () => {
  it('emits updates when slider changes', async () => {
    const wrapper = mount(Allocator, {
      props: {
        categories: ['savings:emergency'],
        modelValue: { 'savings:emergency': 20 },
        availableCents: 200000,
        currencyCode: 'USD',
      },
    })

    const slider = wrapper.find('input[type="range"]')
    await slider.setValue('60')

    const emittedUpdate = wrapper.emitted('update:modelValue')?.pop()?.[0]
    expect(emittedUpdate['savings:emergency']).toBe(60)

    const changeEvent = wrapper.emitted('change')?.pop()?.[0]
    expect(changeEvent.totalPercent).toBe(60)
    expect(changeEvent.totalCents).toBe(120000)
  })
})
