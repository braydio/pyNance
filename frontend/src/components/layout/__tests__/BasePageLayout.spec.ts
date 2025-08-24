// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BasePageLayout from '../BasePageLayout.vue'

describe('BasePageLayout', () => {
  it('uses default padding', () => {
    const wrapper = mount(BasePageLayout, {
      slots: { default: '<div>Content</div>' },
    })
    expect(wrapper.classes()).toContain('p-6')
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('accepts custom padding', () => {
    const wrapper = mount(BasePageLayout, {
      props: { padding: 'p-4' },
      slots: { default: '<div>Content</div>' },
    })
    expect(wrapper.classes()).toContain('p-4')
    expect(wrapper.classes()).not.toContain('p-6')
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('applies gap class when provided', () => {
    const wrapper = mount(BasePageLayout, {
      props: { gap: 4 },
      slots: { default: '<div>A</div><div>B</div>' },
    })
    expect(wrapper.classes()).toContain('gap-4')
    expect(wrapper.html()).toMatchSnapshot()
  })
})
