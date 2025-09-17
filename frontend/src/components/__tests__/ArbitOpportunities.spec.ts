// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ArbitOpportunities from '../ArbitOpportunities.vue'

const { fetchArbitOpportunities } = vi.hoisted(() => ({
  fetchArbitOpportunities: vi.fn(),
}))

vi.mock('@/services/arbit', () => ({
  fetchArbitOpportunities,
}))

beforeEach(() => {
  fetchArbitOpportunities.mockResolvedValue({
    opportunities: [{ id: 1, symbol: 'AAA', profit: 5 }],
  })
})

describe('ArbitOpportunities.vue', () => {
  it('lists opportunities', async () => {
    const wrapper = mount(ArbitOpportunities)
    await flushPromises()
    const rows = wrapper.findAll('[data-testid="opportunity-list"] li')
    expect(rows).toHaveLength(1)
    expect(rows[0].text()).toContain('AAA - 5')
    expect(fetchArbitOpportunities).toHaveBeenCalledTimes(1)
  })
})
