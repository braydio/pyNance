// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import RecurringScanDemo from '../RecurringScanDemo.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {} })
}))

vi.mock('@/api/recurring', () => ({
  scanRecurringTransactions: vi.fn().mockResolvedValue({ actions: [] })
}))

describe('RecurringScanDemo.vue', () => {
  it('matches snapshot', async () => {
    const wrapper = shallowMount(RecurringScanDemo, {
      global: {
        stubs: ['BasePageLayout', 'PageHeader', 'ScanResultsModal', 'ScanResultsTable', 'ScanResultsList', 'Repeat']
      }
    })
    await flushPromises()
    expect(wrapper.html()).toMatchSnapshot()
  })
})
