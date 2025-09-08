// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import TopAccountSnapshot from '../TopAccountSnapshot.vue'

const sampleAccounts = Array.from({ length: 6 }, (_, i) => ({
  id: `acc-${i + 1}`,
  name: `Account ${i + 1}`,
}))

vi.mock('@/composables/useTopAccounts', () => ({
  useTopAccounts: () => ({
    accounts: ref(sampleAccounts),
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

  it('limits account selection to five and fades dropdown', async () => {
    const wrapper = mount(TopAccountSnapshot, {
      global: {
        stubs: { AccountSparkline: true },
      },
    })

    wrapper.vm.addGroup()
    await nextTick()

    const boxes = wrapper.findAll('.bs-account-option input')
    for (let i = 0; i < 5; i++) {
      await boxes[i].setValue(true)
    }
    await nextTick()

    expect(boxes[5].element.disabled).toBe(true)
    const dropdown = wrapper.find('.bs-account-dropdown')
    expect(dropdown.attributes('style')).toContain('opacity: 0.5')
  })
})
