// Simple v-click-outside directive for Vue 3
// Usage: v-click-outside="handler"
// Attaches a document click listener and calls handler when click occurs outside the element
export default {
  beforeMount(el, binding) {
    const handler = (e) => {
      if (!el.contains(e.target)) {
        try {
          binding.value && binding.value(e)
        } catch (err) {
          // no-op
        }
      }
    }
    el.__clickOutside__ = handler
    document.addEventListener('click', handler, true)
    document.addEventListener('touchstart', handler, true)
  },
  unmounted(el) {
    const handler = el.__clickOutside__
    if (handler) {
      document.removeEventListener('click', handler, true)
      document.removeEventListener('touchstart', handler, true)
      delete el.__clickOutside__
    }
  },
}
