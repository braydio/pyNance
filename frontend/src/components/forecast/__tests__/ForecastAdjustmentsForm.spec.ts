// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ForecastAdjustmentsForm from '../ForecastAdjustmentsForm.vue'

describe('ForecastAdjustmentsForm', () => {
  it('gives every field an accessible name instead of relying on placeholders', () => {
    const wrapper = mount(ForecastAdjustmentsForm)
    const fields = wrapper.findAll('input, select')
    expect(fields).toHaveLength(6)
    fields.forEach((field) => expect(field.attributes('aria-label')).toBeTruthy())
    expect(wrapper.get('input[type="number"]').attributes('aria-label')).toContain('dollars')
  })

  it('submits a normalized adjustment and resets the draft', async () => {
    const wrapper = mount(ForecastAdjustmentsForm)
    await wrapper.get('input[type="text"]').setValue('Bonus')
    await wrapper.get('input[type="number"]').setValue(250)
    await wrapper.get('form').trigger('submit')
    const emitted = wrapper.emitted('add-adjustment')?.[0]?.[0] as Record<string, unknown>
    expect(emitted).toMatchObject({
      label: 'Bonus',
      amount: 250,
      frequency: null,
      distribution: 'single',
    })
    expect((wrapper.get('input[type="text"]').element as HTMLInputElement).value).toBe('')
  })
})
