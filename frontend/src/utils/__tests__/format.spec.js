import { describe, expect, it } from 'vitest'
import { amountPolarityClass, formatAmount } from '../format'

describe('format utilities', () => {
  it('formats negative currency with accounting parentheses', () => {
    expect(formatAmount(-20.1)).toBe('($20.10)')
  })

  it('classifies amount polarity for sitewide financial colors', () => {
    expect(amountPolarityClass(42)).toBe('amount-positive')
    expect(amountPolarityClass(-42)).toBe('amount-negative')
    expect(amountPolarityClass(0)).toBe('amount-neutral')
    expect(amountPolarityClass('not-a-number')).toBe('amount-neutral')
  })
})
