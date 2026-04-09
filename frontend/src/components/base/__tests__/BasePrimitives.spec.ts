// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from '../BaseButton.vue'
import BaseInput from '../BaseInput.vue'
import BaseSelect from '../BaseSelect.vue'
import BaseChip from '../BaseChip.vue'
import BasePanel from '../BasePanel.vue'

describe('Base primitives class contracts', () => {
  it('applies button geometry and active state variants', async () => {
    const wrapper = mount(BaseButton, {
      props: { tone: 'accent', variant: 'outline', radius: 'pill', active: true },
      slots: { default: 'Filter' },
    })

    expect(wrapper.classes()).toContain('rounded-full')
    expect(wrapper.classes().join(' ')).toContain('bg-[color:var(--accent-primary)]')

    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('emits updated model values for input and select controls', async () => {
    const input = mount(BaseInput, { props: { modelValue: '', size: 'sm', radius: 'lg' } })
    await input.find('input').setValue('27')
    expect(input.classes()).toContain('ui-radius-3')
    expect(input.emitted('update:modelValue')?.[0]).toEqual(['27'])

    const select = mount(BaseSelect, {
      props: { modelValue: '' },
      slots: { default: '<option value="">All</option><option value="one">One</option>' },
    })
    await select.find('select').setValue('one')
    expect(select.classes()).toContain('ui-radius-2')
    expect(select.emitted('update:modelValue')?.[0]).toEqual(['one'])
    expect(select.emitted('change')).toBeTruthy()
  })

  it('enforces chip and panel radius/surface contracts', () => {
    const chip = mount(BaseChip, {
      props: { tone: 'info', active: true, radius: 'md' },
      slots: { default: 'Info' },
    })
    expect(chip.classes()).toContain('ui-radius-2')
    expect(chip.classes()).toContain('ui-pill-info')

    const panel = mount(BasePanel, {
      props: {
        surface: 'tertiary',
        borderTone: 'accent-cyan',
        radius: 'lg',
        padding: 'sm',
        shadow: 'md',
      },
      slots: { default: 'Panel' },
    })
    expect(panel.classes()).toContain('bg-surface-3')
    expect(panel.classes()).toContain('border-[var(--color-accent-cyan)]')
    expect(panel.classes()).toContain('ui-radius-3')
  })
})
