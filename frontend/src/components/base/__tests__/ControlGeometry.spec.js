// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import BaseInput from '../BaseInput.vue'
import BaseSelect from '../BaseSelect.vue'
import BaseButton from '../BaseButton.vue'
import UiButton from '../../ui/Button.vue'
import DateRangeSelector from '../../DateRangeSelector.vue'

const here = path.dirname(fileURLToPath(import.meta.url))
const mainCss = readFileSync(path.resolve(here, '../../../assets/css/main.css'), 'utf-8')

describe('shared control geometry tokens', () => {
  it('defines the control height, padding and focus tokens', () => {
    expect(mainCss).toMatch(/--control-height:\s*2\.5rem/)
    expect(mainCss).toMatch(/--control-height-sm:\s*2\.25rem/)
    expect(mainCss).toMatch(/--control-padding-x:/)
    expect(mainCss).toMatch(/--control-padding-y:/)
    expect(mainCss).toMatch(/--control-radius:/)
    expect(mainCss).toMatch(/--control-focus-ring:/)
    expect(mainCss).toMatch(/--control-disabled-opacity:/)
  })

  it('shares the same height and padding between .input, .select and .btn', () => {
    const rule = (selector) => {
      const start = mainCss.indexOf(selector)
      return mainCss.slice(start, mainCss.indexOf('}', start))
    }
    ;[rule('.input,\n.select {'), rule('.btn {')].forEach((block) => {
      expect(block).toContain('min-height: var(--control-height)')
      expect(block).toContain('padding: var(--control-padding-y) var(--control-padding-x)')
      expect(block).toContain('border-radius: var(--control-radius)')
    })
  })

  it('keeps native widgets legible per theme and bounds field width', () => {
    expect(mainCss).toContain('color-scheme: dark')
    expect(mainCss).toMatch(/\[data-theme='everforest-light'\]\s*\{\s*color-scheme: light/)
    expect(mainCss).toContain('min-width: 0')
    expect(mainCss).toContain('max-width: 100%')
  })

  it('orders .btn before the color variants so variants keep their colors', () => {
    expect(mainCss.indexOf('\n.btn {')).toBeLessThan(mainCss.indexOf('\n.btn-primary {'))
  })
})

describe('Base controls', () => {
  it('BaseInput and BaseSelect share the same height tokens and text size per size', () => {
    ;['md', 'sm'].forEach((size) => {
      const input = mount(BaseInput, { props: { size } })
      const select = mount(BaseSelect, { props: { size } })
      const button = mount(BaseButton, { props: { size } })
      const height =
        size === 'md' ? 'min-h-[var(--control-height)]' : 'min-h-[var(--control-height-sm)]'
      ;[input, select, button].forEach((wrapper) => {
        expect(wrapper.classes()).toContain(height)
        expect(wrapper.classes()).toContain('text-sm') // labels/fields >= 0.875rem
        expect(wrapper.classes()).not.toContain('text-xs')
      })
      expect(input.classes()).toContain('min-w-0')
      expect(select.classes()).toContain('max-w-full')
    })
  })

  it('uses the accessible control border, not the decorative divider', () => {
    const input = mount(BaseInput)
    expect(input.classes().join(' ')).toContain('border-[color:var(--control-border)]')
  })

  it('associates invalid state and error text via aria attributes', () => {
    const input = mount(BaseInput, { props: { invalid: true, describedby: 'amount-error' } })
    expect(input.attributes('aria-invalid')).toBe('true')
    expect(input.attributes('aria-describedby')).toBe('amount-error')
    const select = mount(BaseSelect, { props: { invalid: true, describedby: 'x' } })
    expect(select.attributes('aria-invalid')).toBe('true')

    const clean = mount(BaseInput)
    expect(clean.attributes('aria-invalid')).toBeUndefined()
    expect(clean.attributes('aria-describedby')).toBeUndefined()
  })

  it('keeps v-model, enter and click semantics', async () => {
    const input = mount(BaseInput, { props: { modelValue: '' } })
    await input.setValue('42')
    expect(input.emitted('update:modelValue')[0]).toEqual(['42'])
    await input.trigger('keyup.enter')
    expect(input.emitted('enter')).toHaveLength(1)

    const button = mount(BaseButton, { slots: { default: 'Go' } })
    expect(button.attributes('type')).toBe('button')
    await button.trigger('click')
    expect(button.emitted('click')).toHaveLength(1)
  })
})

describe('UiButton', () => {
  it('is non-submitting by default and honors an explicit submit', () => {
    expect(mount(UiButton).attributes('type')).toBe('button')
    expect(mount(UiButton, { props: { type: 'submit' } }).attributes('type')).toBe('submit')
  })

  it('emits click once and does not click while disabled', async () => {
    const wrapper = mount(UiButton, { props: { variant: 'outline' }, slots: { default: 'Save' } })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
    expect(wrapper.classes()).toEqual(expect.arrayContaining(['btn', 'btn-outline']))

    const disabled = mount(UiButton, { props: { disabled: true } })
    await disabled.trigger('click')
    expect(disabled.emitted('click')).toBeUndefined()
  })
})

describe('DateRangeSelector', () => {
  it('labels both dates, wraps responsively and shares the field class', () => {
    const wrapper = mount(DateRangeSelector, {
      props: { startDate: '2025-01-01', endDate: '2025-01-31' },
    })
    expect(wrapper.text()).toContain('From')
    expect(wrapper.text()).toContain('Through')
    const inputs = wrapper.findAll('input[type="date"]')
    expect(inputs).toHaveLength(2)
    inputs.forEach((input) => expect(input.classes()).toContain('input'))
    expect(wrapper.classes()).toContain('date-range-selector')
    expect(wrapper.findAll('label')).toHaveLength(2)
  })

  it('keeps the range ordered when the start passes the end', async () => {
    const wrapper = mount(DateRangeSelector, {
      props: { startDate: '2025-01-01', endDate: '2025-01-31' },
    })
    await wrapper.findAll('input')[0].setValue('2025-02-10')
    expect(wrapper.emitted('update:endDate')[0]).toEqual(['2025-02-10'])
    expect(wrapper.emitted('update:startDate')[0]).toEqual(['2025-02-10'])
  })
})
