// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PageHeader from '../PageHeader.vue'
import { defineComponent } from 'vue'

describe('PageHeader', () => {
  it('renders title slot', () => {
    const wrapper = mount(PageHeader, {
      slots: { title: 'Dashboard' }
    })
    expect(wrapper.find('h1').text()).toBe('Dashboard')
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('renders optional subtitle and icon', () => {
    const Icon = defineComponent({ template: '<span class="icon" />' })
    const wrapper = mount(PageHeader, {
      props: { icon: Icon },
      slots: {
        title: 'Accounts',
        subtitle: 'Overview'
      }
    })
    expect(wrapper.find('p').text()).toBe('Overview')
    expect(wrapper.find('.icon').exists()).toBe(true)
  })

  it('renders actions slot', () => {
    const wrapper = mount(PageHeader, {
      slots: {
        title: 'Settings',
        actions: '<button class="action">Act</button>'
      }
    })
    expect(wrapper.find('.action').exists()).toBe(true)
  })
})
