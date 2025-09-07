// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'

vi.mock('@/services/arbit', () => ({
  startArbit: vi.fn().mockResolvedValue({}),
  stopArbit: vi.fn().mockResolvedValue({}),
  fetchArbitStatus: vi.fn().mockResolvedValue({ running: false }),
}))

import { startArbit, stopArbit } from '@/services/arbit'
import ArbitControls from '../ArbitControls.vue'

describe('ArbitControls.vue', () => {
  it('calls start and stop services', async () => {
    const wrapper = mount(ArbitControls)
    await flushPromises()
    await wrapper.find('button.start-btn').trigger('click')
    await wrapper.find('button.stop-btn').trigger('click')
    expect(startArbit).toHaveBeenCalled()
    expect(stopArbit).toHaveBeenCalled()
  })
})
