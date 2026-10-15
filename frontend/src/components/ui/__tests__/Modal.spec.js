// @vitest-environment jsdom
import { describe, it, expect, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import Modal from '../Modal.vue'

const mounted = []

function mountModal(props = {}, slots = {}) {
  const wrapper = mount(Modal, {
    props,
    slots: {
      title: 'Delete account?',
      body: '<p>Body</p><input id="first" /><button id="last" type="button">Last</button>',
      ...slots,
    },
    attachTo: document.body,
  })
  mounted.push(wrapper)
  return wrapper
}

const dialog = () => document.body.querySelector('[role="dialog"]')

afterEach(() => {
  while (mounted.length) {
    const wrapper = mounted.pop()
    try {
      wrapper.unmount()
    } catch {
      // already unmounted by the test
    }
  }
  document.body.innerHTML = ''
  document.body.style.overflow = ''
})

describe('Modal', () => {
  it('teleports a labelled, modal dialog to the body', async () => {
    const wrapper = mountModal()
    await nextTick()
    const el = dialog()
    expect(el).toBeTruthy()
    expect(wrapper.element.contains(el)).toBe(false) // rendered outside the component root
    expect(document.body.contains(el)).toBe(true)
    expect(el.getAttribute('aria-modal')).toBe('true')
    const titleId = el.getAttribute('aria-labelledby')
    expect(document.getElementById(titleId).textContent).toContain('Delete account?')
    const close = el.querySelector('button.modal-close')
    expect(close.getAttribute('type')).toBe('button')
    expect(close.getAttribute('aria-label')).toBe('Close dialog')
    wrapper.unmount()
  })

  it('moves focus into the dialog, traps Tab and returns focus on close', async () => {
    const opener = document.createElement('button')
    document.body.appendChild(opener)
    opener.focus()

    const wrapper = mountModal()
    await nextTick()
    await nextTick()
    const el = dialog()
    expect(el.contains(document.activeElement)).toBe(true)

    const last = el.querySelector('#last')
    last.focus()
    last.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }),
    )
    expect(document.activeElement).toBe(el.querySelector('button.modal-close'))

    el.querySelector('button.modal-close').dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true, cancelable: true }),
    )
    expect(document.activeElement).toBe(last)

    wrapper.unmount()
    await nextTick()
    await nextTick()
    expect(document.activeElement).toBe(opener)
  })

  it('closes on Escape, backdrop click and the close button but not on dialog clicks', async () => {
    const wrapper = mountModal()
    await nextTick()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(wrapper.emitted('close')).toHaveLength(1)

    document.body.querySelector('[data-testid="modal-backdrop"]').click()
    expect(wrapper.emitted('close')).toHaveLength(2)

    dialog().click()
    expect(wrapper.emitted('close')).toHaveLength(2)

    document.body.querySelector('button.modal-close').click()
    expect(wrapper.emitted('close')).toHaveLength(3)
    wrapper.unmount()
  })

  it('locks body scroll while open and restores it afterwards', async () => {
    document.body.style.overflow = 'auto'
    const wrapper = mountModal()
    await nextTick()
    expect(document.body.style.overflow).toBe('hidden')
    wrapper.unmount()
    expect(document.body.style.overflow).toBe('auto')
  })

  it('only the top-most stacked dialog handles Escape and the scroll lock is reference counted', async () => {
    const outer = mountModal()
    const inner = mountModal()
    await nextTick()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    expect(inner.emitted('close')).toHaveLength(1)
    expect(outer.emitted('close')).toBeUndefined()

    inner.unmount()
    expect(document.body.style.overflow).toBe('hidden') // outer still open
    outer.unmount()
    expect(document.body.style.overflow).toBe('')
  })

  it('bounds size to the viewport, scrolls the body region and keeps the footer visible', async () => {
    const wrapper = mountModal(
      { size: 'md' },
      { footer: '<button type="button" id="confirm">Delete</button>' },
    )
    await nextTick()
    const el = dialog()
    expect(el.style.getPropertyValue('--modal-max-width')).toBe('28rem')
    expect(el.querySelector('.modal-body')).toBeTruthy()
    const footer = el.querySelector('.modal-footer')
    expect(footer.querySelector('#confirm')).toBeTruthy()
    expect(footer.closest('.modal-body')).toBeNull() // footer is outside the scrolling region
    wrapper.unmount()
  })
})
