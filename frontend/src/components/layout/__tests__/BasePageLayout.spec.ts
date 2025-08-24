// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BasePageLayout from '../BasePageLayout.vue'

describe('BasePageLayout', () => {
  it('renders with default padding and gap', () => {
    const wrapper = mount(BasePageLayout)
    expect(wrapper.classes()).toContain('p-6')
    expect(wrapper.classes()).toContain('gap-6')
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('applies custom padding', () => {
    const wrapper = mount(BasePageLayout, { props: { padding: 'p-2' } })
    expect(wrapper.classes()).toContain('p-2')
    expect(wrapper.classes()).not.toContain('p-6')
  })

  it('can disable padding', () => {
    const wrapper = mount(BasePageLayout, { props: { padding: false } })
    expect(wrapper.classes()).not.toContain('p-6')
  })

  it('applies gap prop', () => {
    const wrapper = mount(BasePageLayout, { props: { gap: 'gap-4' } })
    expect(wrapper.classes()).toContain('gap-4')
  })
})
