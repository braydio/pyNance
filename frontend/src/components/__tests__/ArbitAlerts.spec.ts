// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'

import ArbitAlerts from '../ArbitAlerts.vue'

class EventSourceMock {
  onmessage: ((e: MessageEvent) => void) | null = null
  constructor(public url: string) {}
  close = vi.fn()
  emit(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent)
  }
}

describe('ArbitAlerts.vue', () => {
  it('renders alert from backend events', async () => {
    const mock = new EventSourceMock('')
    ;(globalThis as any).EventSource = vi.fn(() => mock)
    const wrapper = mount(ArbitAlerts)
    mock.emit({ net_profit_percent: 7, threshold: 5 })
    await nextTick()
    expect(wrapper.text()).toContain('7')
  })
})
