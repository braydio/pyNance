// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'
import {
  DEFAULT_THEME,
  THEME_STORAGE_KEY,
  initializeTheme,
  normalizeTheme,
  setTheme,
  useTheme,
} from '../useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.removeAttribute('style')
  })

  it('normalizes unsupported theme identifiers', () => {
    expect(normalizeTheme('everforest-light')).toBe('everforest-light')
    expect(normalizeTheme('unknown')).toBe(DEFAULT_THEME)
  })

  it('applies and persists a selected theme', () => {
    setTheme('everforest-light')

    expect(document.documentElement.dataset.theme).toBe('everforest-light')
    expect(document.documentElement.style.colorScheme).toBe('light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('everforest-light')
    expect(useTheme().activeTheme.value).toBe('everforest-light')
  })

  it('restores a saved theme during initialization', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'everforest-light')

    expect(initializeTheme()).toBe('everforest-light')
    expect(document.documentElement.dataset.theme).toBe('everforest-light')
  })
})
