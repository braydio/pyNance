// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ArbitStatus from '../ArbitStatus.vue'

vi.mock('@/services/arbit', () => ({
  fetchArbitStatus: vi.fn().mockResolvedValue({ running: true }),
}))

describe('ArbitStatus.vue', () => {
  it('shows running status', async () => {
    const wrapper = mount(ArbitStatus)
    await flushPromises()
    expect(wrapper.text()).toContain('running')
  })
})
