// src/composables/useForecastEngine.ts

import { computed } from 'vue'

interface RecurringTransaction {
  label: string
  amount: number
  frequency: 'weekly' | 'monthly'
  nextDueDate: string // ISO date
}

interface AccountBalance {
  date: string // ISO date
  balance: number
}

function generateLabels(viewType: 'Month' | 'Year'): string[] {
  const labels: string[] = []
  const today = new Date()
  if (viewType === 'Month') {
    for (let i = 0; i < 30; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      labels.push(date.toISOString().split('T')[0])
    }
  } else if (viewType === 'Year') {
    for (let i = 0; i < 12; i++) {
      const date = new Date(today)
      date.setMonth(today.getMonth() + i)
      labels.push(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`)
    }
  }
  return labels
}

function computeActualLine(labels: string[], history: AccountBalance[]): number[] {
  const historyMap = new Map(history.map(h => [h.date, h.balance]))
  return labels.map(label => historyMap.get(label) ?? null)
}

function computeForecastLine(
  labels: string[],
  recurringTxs: RecurringTransaction[],
  manualIncome: number,
  liabilityRate: number
): number[] {
  const forecast = Array(labels.length).fill(0)
  const labelDates = labels.map(label => new Date(label))

  recurringTxs.forEach(tx => {
    const startDate = new Date(tx.nextDueDate)
    const interval = tx.frequency === 'weekly' ? 7 : 30
    labelDates.forEach((date, index) => {
      if (date >= startDate && (date.getTime() - startDate.getTime()) % (interval * 86400000) === 0) {
        forecast[index] += tx.amount
      }
    })
  })

  return forecast.map(value => value + manualIncome - liabilityRate)
}

export function useForecastEngine(
  viewType: 'Month' | 'Year',
  recurringTxs: RecurringTransaction[],
  accountHistory: AccountBalance[],
  manualIncome: number = 0,
  liabilityRate: number = 0
) {
  const labels = generateLabels(viewType)
  const actualLine = computeActualLine(labels, accountHistory)
  const forecastLine = computeForecastLine(labels, recurringTxs, manualIncome, liabilityRate)

  return {
    labels,
    actualLine,
    forecastLine
  }
}

