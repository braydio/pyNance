// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

vi.mock('@/composables/useTopAccounts', () => ({
  useTopAccounts: () => ({
    allVisibleAccounts: ref([]),
    fetchAccounts: vi.fn(),
  }),
}))

describe('TopAccountSnapshot group editing', () => {
  it('renders input for new group and saves name on blur', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: {
        stubs: { AccountSparkline: true },
      },
    })

    wrapper.vm.addGroup()
    await nextTick()

    const input = wrapper.find('input.bs-tab')
    expect(input.exists()).toBe(true)

    await input.setValue('Test Group')
    await input.trigger('blur')
    await nextTick()

    const texts = wrapper.findAll('button.bs-tab').map((b) => b.text())
    expect(texts).toContain('Test Group')
  })
})
