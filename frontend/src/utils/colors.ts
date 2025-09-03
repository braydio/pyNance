// frontend/src/utils/colors.ts
/**
 * Utilities for accessing accent color values defined by the theme.
 *
 * Colors are exposed as CSS custom properties on the document root.
 * These helpers return the resolved values so components can render
 * charts and widgets with theme-aware palettes.
 */
export const ACCENT_COLOR_VARS = [
  '--color-accent-cyan',
  '--color-accent-magenta',
  '--color-accent-yellow',
  '--color-accent-blue',
  '--color-accent-orange',
  '--color-accent-green',
  '--color-accent-purple',
  '--color-accent-red',
  // Repeat a second pass for larger palettes without adjacent similarity
  '--color-accent-cyan',
  '--color-accent-magenta',
] as const

/**
 * Retrieve the CSS color value for the given accent index.
 *
 * @param index - Position within {@link ACCENT_COLOR_VARS}.
 * @returns The computed color string from the document root.
 */
export function getAccentColor(index: number): string {
  const name = ACCENT_COLOR_VARS[index % ACCENT_COLOR_VARS.length]
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
