import { describe, it, expect } from 'vitest'
import { formatAmount, formatForecastMoney, formatSignedCashflow } from '../format'

describe('formatSignedCashflow', () => {
  it.each([
    [1234.56, '+$1,234.56'],
    [-25.4, '−$25.40'],
    [0, '$0.00'],
    [-0, '$0.00'],
    [0.004, '+$0.00'],
    ['1200', '+$1,200.00'],
    [-1234567.891, '−$1,234,567.89'],
  ])('%s -> %s', (input, expected) => {
    expect(formatSignedCashflow(input)).toBe(expected)
  })

  it('can omit the plus sign and never invents zero for missing data', () => {
    expect(formatSignedCashflow(10, { showPlus: false })).toBe('$10.00')
    expect(formatSignedCashflow(-10, { showPlus: false })).toBe('−$10.00')
    for (const bad of [null, undefined, '', 'abc', NaN, Infinity]) {
      expect(formatSignedCashflow(bad)).toBe('Unavailable')
    }
  })
})

describe('formatForecastMoney', () => {
  it('formats balances with grouping and keeps a plain minus', () => {
    expect(formatForecastMoney(11686.65)).toBe('$11,686.65')
    expect(formatForecastMoney(0)).toBe('$0.00')
    expect(formatForecastMoney(-45.2)).toBe('-$45.20')
    expect(formatForecastMoney('2500')).toBe('$2,500.00')
  })

  it('says Unavailable instead of $0.00 for missing data', () => {
    for (const bad of [null, undefined, '', 'x', NaN, -Infinity]) {
      expect(formatForecastMoney(bad)).toBe('Unavailable')
    }
  })
})

describe('formatAmount contract is unchanged', () => {
  it('still uses accounting parentheses for negatives', () => {
    expect(formatAmount(-45.2)).toBe('($45.20)')
    expect(formatAmount(1200)).toBe('$1,200.00')
  })
})
