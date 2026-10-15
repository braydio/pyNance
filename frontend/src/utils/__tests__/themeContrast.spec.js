// Contrast guard for the semantic foreground tokens in both palettes.
// Computes WCAG 2.x ratios from the literal values in styles/theme.css (no browser needed);
// translucent (rgba) tokens are intentionally not part of these solid-color checks.
import { readFileSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { describe, it, expect } from 'vitest'

const here = path.dirname(fileURLToPath(import.meta.url))
const css = readFileSync(path.resolve(here, '../../styles/theme.css'), 'utf-8')

function block(selector) {
  const start = css.indexOf(selector)
  const open = css.indexOf('{', start)
  const close = css.indexOf('\n}', open)
  return css.slice(open + 1, close)
}

function parseTokens(body) {
  const tokens = {}
  for (const match of body.matchAll(/(--[\w-]+):\s*([^;]+?)(?:\s*\/\*.*?\*\/)?;/gs)) {
    tokens[match[1]] = match[2].replace(/\s+/g, ' ').trim()
  }
  return tokens
}

const dark = parseTokens(block(':root {'))
const light = { ...dark, ...parseTokens(block(":root[data-theme='everforest-light']")) }

const toRgb = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))

function resolve(tokens, value, depth = 0) {
  if (depth > 10) throw new Error(`Unresolvable: ${value}`)
  const v = value.trim()
  if (/^#[0-9a-f]{6}$/i.test(v)) return toRgb(v)
  const ref = v.match(/^var\((--[\w-]+)\)$/)
  if (ref) return resolve(tokens, tokens[ref[1]], depth + 1)
  const mix = v.match(/^color-mix\(in srgb, (.+?) (\d+(?:\.\d+)?)%, (.+)\)$/)
  if (mix) {
    const a = resolve(tokens, mix[1], depth + 1)
    const pa = Number(mix[2])
    let second = mix[3]
    const secondPct = second.match(/^(.+) (\d+(?:\.\d+)?)%$/)
    if (secondPct) second = secondPct[1]
    const b = resolve(tokens, second, depth + 1)
    return a.map((c, i) => (c * pa) / 100 + (b[i] * (100 - pa)) / 100)
  }
  throw new Error(`Unsupported color: ${value}`)
}

function luminance([r, g, b]) {
  const f = (c) => {
    const s = c / 255
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4
  }
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)
}

function ratio(foreground, background) {
  const [hi, lo] = [luminance(foreground), luminance(background)].sort((a, b) => b - a)
  return (hi + 0.05) / (lo + 0.05)
}

// Surfaces that carry body text in both themes.
const SURFACES = [
  '--page-bg',
  '--color-bg',
  '--color-bg-secondary',
  '--surface-1',
  '--surface-2',
  '--surface-3',
  '--input-bg',
]
// Light-theme table surfaces are plain hex and held to the same bar.
const LIGHT_ONLY_SURFACES = [
  '--table-surface',
  '--table-surface-alt',
  '--table-surface-strong',
  '--table-header',
]

const THEMES = [
  ['nightfox', dark, SURFACES],
  ['everforest-light', light, [...SURFACES, ...LIGHT_ONLY_SURFACES]],
]

const TEXT_ROLES = [
  '--text-primary',
  '--text-secondary',
  '--text-muted',
  '--text-positive',
  '--text-negative',
  '--text-warning',
  '--text-link',
]

describe.each(THEMES)('%s theme contrast', (_name, tokens, surfaces) => {
  it.each(TEXT_ROLES)('%s is >= 4.5:1 on every body surface', (role) => {
    surfaces.forEach((surface) => {
      const value = ratio(resolve(tokens, tokens[role]), resolve(tokens, tokens[surface]))
      expect(value, `${role} on ${surface}`).toBeGreaterThanOrEqual(4.5)
    })
  })

  it('keeps essential control outlines >= 3:1 against the control and its surface', () => {
    const border = resolve(tokens, tokens['--control-border'])
    ;['--input-bg', '--surface-1', '--surface-2', '--page-bg'].forEach((surface) => {
      expect(ratio(border, resolve(tokens, tokens[surface])), surface).toBeGreaterThanOrEqual(3)
    })
  })

  it('keeps muted text visibly weaker than primary text', () => {
    const page = resolve(tokens, tokens['--page-bg'])
    expect(ratio(resolve(tokens, tokens['--text-muted']), page)).toBeLessThan(
      ratio(resolve(tokens, tokens['--text-primary']), page),
    )
  })

  it('keeps chart accent identities defined for backwards compatibility', () => {
    ;[
      '--color-accent-green',
      '--color-accent-red',
      '--color-accent-cyan',
      '--color-success',
      '--color-error',
    ].forEach((token) => expect(tokens[token]).toBeTruthy())
  })
})
