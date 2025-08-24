// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PageHeader from '../PageHeader.vue'

describe('PageHeader', () => {
  it('renders title', () => {
    const wrapper = mount(PageHeader, {
      slots: { title: 'Dashboard' },
    })
    expect(wrapper.find('h1').text()).toBe('Dashboard')
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('renders optional subtitle and icon', () => {
    const wrapper = mount(PageHeader, {
      slots: {
        title: 'Dashboard',
        subtitle: 'Overview',
        icon: '<span class="icon" />',
      },
    })
    expect(wrapper.find('p.text-muted').text()).toBe('Overview')
    expect(wrapper.find('.icon').exists()).toBe(true)
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('renders actions slot', () => {
    const wrapper = mount(PageHeader, {
      slots: {
        title: 'Dashboard',
        actions: '<button>Action</button>',
      },
    })
    expect(wrapper.find('div.flex.items-center.gap-2.ml-auto').exists()).toBe(true)
    expect(wrapper.html()).toMatchSnapshot()
  })
})
