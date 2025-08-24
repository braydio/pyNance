// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import Planning from '../Planning.vue'

vi.mock('@/composables/usePlanning', () => ({
  usePlanning: () => ({ state: {} })
}))

describe('Planning.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(Planning, {
      global: {
        stubs: ['BasePageLayout', 'PageHeader', 'Calendar']
      }
    })
    expect(wrapper.html()).toMatchSnapshot()
  })
})
