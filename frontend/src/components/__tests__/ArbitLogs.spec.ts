// @vitest-environment jsdom
import { mount, flushPromises } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

vi.mock('@/services/arbit', () => ({
  fetchArbitLogs: vi.fn().mockResolvedValue({
    lines: ['alpha', 'beta'],
    last_updated: '2024-01-01T00:00:00Z',
    limit: 50,
  }),
}))

import { fetchArbitLogs } from '@/services/arbit'
import ArbitLogs from '../ArbitLogs.vue'

type FetchLogsMock = vi.MockedFunction<typeof fetchArbitLogs>

const mockedFetchLogs = fetchArbitLogs as FetchLogsMock

describe('ArbitLogs.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.runOnlyPendingTimers()
    vi.useRealTimers()
  })

  it('renders returned log entries', async () => {
    const wrapper = mount(ArbitLogs)
    await flushPromises()

    expect(mockedFetchLogs).toHaveBeenCalled()
    const rows = wrapper.findAll('.log-line')
    expect(rows).toHaveLength(2)
    expect(wrapper.text()).toContain('alpha')
    expect(wrapper.text()).toContain('beta')

    wrapper.unmount()
  })

  it('shows a friendly error when logs cannot load', async () => {
    mockedFetchLogs.mockRejectedValueOnce(new Error('boom'))

    const wrapper = mount(ArbitLogs)
    await flushPromises()

    expect(wrapper.text()).toContain('Unable to load logs right now.')

    wrapper.unmount()
  })
})
