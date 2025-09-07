// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ArbitTrades from '../ArbitTrades.vue'

vi.mock('@/services/arbit', () => ({
  fetchArbitTrades: vi.fn().mockResolvedValue({
    trades: [{ id: 1, pair: 'AAA/BBB', profit: 1 }],
  }),
}))

describe('ArbitTrades.vue', () => {
  it('renders trades table', async () => {
    const wrapper = mount(ArbitTrades)
    await flushPromises()
    const rows = wrapper.findAll('tbody tr')
    expect(rows).toHaveLength(1)
    expect(rows[0].text()).toContain('AAA/BBB')
  })
})
