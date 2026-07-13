// Ensure localStorage is available in Node v22+ where the built-in
// localStorage requires --localstorage-file.  jsdom provides its own
// implementation through window.localStorage; expose it as a global
// so tests can call localStorage.clear() etc. without crashing.
if (typeof localStorage === 'undefined' || typeof localStorage.clear !== 'function') {
  const { JSDOM } = require('jsdom')
  const dom = new JSDOM('', { url: 'http://localhost' })
  // Place jsdom's localStorage on the globalThis so every test sees it.
  // eslint-disable-next-line no-undef
  globalThis.localStorage = dom.window.localStorage
}
