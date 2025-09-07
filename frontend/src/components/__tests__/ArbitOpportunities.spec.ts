// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ArbitOpportunities from '../ArbitOpportunities.vue'

vi.mock('@/services/arbit', () => ({
  fetchArbitOpportunities: vi.fn().mockResolvedValue({
    opportunities: [{ id: 1, symbol: 'AAA', profit: 5 }],
  }),
}))

describe('ArbitOpportunities.vue', () => {
  it('lists opportunities', async () => {
    const wrapper = mount(ArbitOpportunities)
    await flushPromises()
    expect(wrapper.text()).toContain('AAA')
  })
})
