// @vitest-environment jsdom
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

  it('offers an aligned percent field per category that stays in sync with the slider', async () => {
    const wrapper = mount(Allocator, {
      props: {
        categories: ['savings:emergency', 'goal:vacation'],
        modelValue: { 'savings:emergency': 20, 'goal:vacation': 10 },
        availableCents: 100000,
        currencyCode: 'USD',
      },
    })

    const number = wrapper.get('[data-testid="allocator-number-goal:vacation"]')
    expect((number.element as HTMLInputElement).value).toBe('10')
    await number.setValue('40')
    const slider = wrapper.findAll('input[type="range"]')[1]
    expect((slider.element as HTMLInputElement).value).toBe('40')
    expect(wrapper.get('[data-testid="allocator-row-goal:vacation"]').text()).toContain('$400.00')
  })

  it('announces a live total and remaining amount and flags over-allocation', async () => {
    const wrapper = mount(Allocator, {
      props: {
        categories: ['a', 'b'],
        modelValue: { a: 30, b: 30 },
        availableCents: 100000,
        currencyCode: 'USD',
      },
    })
    const summary = wrapper.get('[data-testid="allocation-summary"]')
    expect(summary.attributes('role')).toBe('status')
    expect(summary.attributes('aria-live')).toBe('polite')
    expect(summary.text()).toContain('60%')
    expect(summary.text()).toContain('40% remaining')
    expect(summary.text()).toContain('$400.00 unassigned')
    expect(summary.classes()).not.toContain('is-invalid')
  })
})
