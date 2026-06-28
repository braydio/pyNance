import { computed, ref } from 'vue'

export const DEFAULT_THEME = 'nightfox'
export const THEME_STORAGE_KEY = 'pynance-theme'
export const THEMES = Object.freeze([
  {
    id: 'nightfox',
    label: 'Nightfox',
    description: 'Deep blue surfaces with warm, luminous accents.',
  },
  {
    id: 'everforest-light',
    label: 'Everforest Light',
    description: 'Pale green surfaces with calm forest-toned accents.',
  },
])

const supportedThemeIds = new Set(THEMES.map(({ id }) => id))
const activeTheme = ref(DEFAULT_THEME)

/**
 * Return a supported theme id, falling back to the application default.
 *
 * @param {string | null | undefined} themeId Candidate theme identifier.
 * @returns {string} A supported theme identifier.
 */
export function normalizeTheme(themeId) {
  return supportedThemeIds.has(themeId) ? themeId : DEFAULT_THEME
}

/**
 * Apply and persist a theme selection.
 *
 * @param {string} themeId Theme identifier to apply.
 * @returns {string} The normalized theme identifier that was applied.
 */
export function setTheme(themeId) {
  const normalizedTheme = normalizeTheme(themeId)
  activeTheme.value = normalizedTheme

  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = normalizedTheme
    document.documentElement.style.colorScheme =
      normalizedTheme === 'everforest-light' ? 'light' : 'dark'
  }

  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(THEME_STORAGE_KEY, normalizedTheme)
  }

  return normalizedTheme
}

/**
 * Restore the saved theme before the application mounts.
 *
 * @returns {string} The restored or default theme identifier.
 */
export function initializeTheme() {
  const savedTheme =
    typeof localStorage === 'undefined' ? null : localStorage.getItem(THEME_STORAGE_KEY)
  return setTheme(savedTheme)
}

/**
 * Expose reactive theme state and actions to Vue components.
 *
 * @returns {{activeTheme: import('vue').Ref<string>, isLightTheme: import('vue').ComputedRef<boolean>, setTheme: typeof setTheme, themes: typeof THEMES}}
 * Theme state and supported theme metadata.
 */
export function useTheme() {
  return {
    activeTheme,
    isLightTheme: computed(() => activeTheme.value === 'everforest-light'),
    setTheme,
    themes: THEMES,
  }
}
