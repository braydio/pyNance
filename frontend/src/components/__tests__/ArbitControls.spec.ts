// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/services/arbit', () => ({
  startArbit: vi.fn().mockResolvedValue({}),
  stopArbit: vi.fn().mockResolvedValue({}),
  fetchArbitStatus: vi.fn().mockResolvedValue({ running: false }),
  postArbitAlert: vi.fn().mockResolvedValue({}),
}))

import { startArbit, stopArbit } from '@/services/arbit'
import ArbitControls from '../ArbitControls.vue'

describe('ArbitControls.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('requires spread and fee before starting the engine', async () => {
    const wrapper = mount(ArbitControls)
    await flushPromises()

    await wrapper.find('button.start-btn').trigger('click')
    await flushPromises()

    expect(startArbit).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Enter the minimum spread percentage required to start trading.')
    expect(wrapper.text()).toContain('Provide the expected percentage cost of executing the trade.')
  })

  it('calls start and stop services with configured inputs', async () => {
    const wrapper = mount(ArbitControls)
    await flushPromises()

    await wrapper.find('[data-test="start-threshold"]').setValue('0.5')
    await wrapper.find('[data-test="start-fee"]').setValue('0.15')

    await wrapper.find('button.start-btn').trigger('click')
    await flushPromises()

    expect(startArbit).toHaveBeenCalledWith(0.5, 0.15)

    await wrapper.find('button.stop-btn').trigger('click')
    await flushPromises()

    expect(stopArbit).toHaveBeenCalled()
  })
})
