// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import ArbitrageLive from '../ArbitrageLive.vue'

vi.mock('@/api/arbitrage', () => ({
  fetchArbitrageData: vi.fn().mockResolvedValue({ content: '' })
}))

describe('ArbitrageLive.vue', () => {
  it('matches snapshot', () => {
    const wrapper = shallowMount(ArbitrageLive, {
      global: {
        stubs: ['BasePageLayout', 'PageHeader', 'Activity']
      }
    })
    expect(wrapper.html()).toMatchSnapshot()
  })
})
