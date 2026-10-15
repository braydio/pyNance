/**
 * useModalA11y
 *
 * Shared dialog behavior: while active it locks body scroll (reference counted so stacked
 * dialogs cooperate), moves focus into the dialog, traps Tab, handles Escape for the
 * top-most dialog only, and returns focus to the previously focused element when closed.
 */
import { nextTick, onBeforeUnmount, onMounted, unref, watch } from 'vue'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

let scrollLocks = 0
let previousOverflow = ''
const stack = []

/** Lock page scroll; call the returned function (once) to release. */
export function lockBodyScroll() {
  if (typeof document === 'undefined') return () => {}
  if (scrollLocks === 0) {
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
  }
  scrollLocks += 1
  let released = false
  return () => {
    if (released) return
    released = true
    scrollLocks = Math.max(scrollLocks - 1, 0)
    if (scrollLocks === 0) document.body.style.overflow = previousOverflow
  }
}

function visibleFocusables(root) {
  return Array.from(root.querySelectorAll(FOCUSABLE)).filter(
    (el) => !el.hasAttribute('hidden') && el.getAttribute('aria-hidden') !== 'true',
  )
}

/**
 * @param {object} options
 * @param {import('vue').Ref<HTMLElement|null>} options.dialogRef Dialog container element.
 * @param {import('vue').Ref<boolean>|boolean} [options.active] Whether the dialog is open.
 * @param {(event: KeyboardEvent) => (boolean|void)} [options.onEscape] Return true when handled.
 */
export function useModalA11y({ dialogRef, active = true, onEscape } = {}) {
  let releaseScroll = null
  let previousFocus = null
  const entry = {}

  function onKeydown(event) {
    if (stack[stack.length - 1] !== entry) return
    const dialog = unref(dialogRef)
    if (!dialog) return

    if (event.key === 'Escape') {
      const handled = onEscape ? onEscape(event) : false
      if (handled) {
        event.preventDefault()
        event.stopPropagation()
      }
      return
    }

    if (event.key === 'Tab') {
      const items = visibleFocusables(dialog)
      if (!items.length) {
        event.preventDefault()
        dialog.focus?.()
        return
      }
      const first = items[0]
      const last = items[items.length - 1]
      const current = document.activeElement
      if (event.shiftKey && (current === first || !dialog.contains(current))) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && (current === last || !dialog.contains(current))) {
        event.preventDefault()
        first.focus()
      }
    }
  }

  function activate() {
    if (entry.open) return
    entry.open = true
    previousFocus = document.activeElement
    releaseScroll = lockBodyScroll()
    stack.push(entry)
    document.addEventListener('keydown', onKeydown)
    nextTick(() => {
      const dialog = unref(dialogRef)
      if (!dialog) return
      const [first] = visibleFocusables(dialog)
      ;(first || dialog).focus?.()
    })
  }

  function deactivate() {
    if (!entry.open) return
    entry.open = false
    document.removeEventListener('keydown', onKeydown)
    const index = stack.indexOf(entry)
    if (index !== -1) stack.splice(index, 1)
    releaseScroll?.()
    releaseScroll = null
    const target = previousFocus
    previousFocus = null
    if (target && typeof target.focus === 'function' && document.contains(target)) {
      nextTick(() => target.focus())
    }
  }

  onMounted(() => {
    if (unref(active)) activate()
  })
  watch(
    () => unref(active),
    (isActive) => (isActive ? activate() : deactivate()),
  )
  onBeforeUnmount(deactivate)

  return { activate, deactivate }
}
