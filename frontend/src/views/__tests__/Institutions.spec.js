// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Institutions from '../Institutions.vue'
import BasePageLayout from '@/components/layout/BasePageLayout.vue'

describe('Institutions view', () => {
  it('renders exactly one page wrapper so vertical padding is not doubled', () => {
    const wrapper = shallowMount(Institutions, {
      global: { stubs: { BasePageLayout: false, PageHeader: true, InstitutionTable: true } },
    })
    expect(wrapper.findAllComponents(BasePageLayout)).toHaveLength(1)
    expect(wrapper.findAll('.py-6')).toHaveLength(1)
    const html = wrapper.html()
    expect(html.indexOf('page-header')).toBeLessThan(html.indexOf('institution-table'))
  })
})
