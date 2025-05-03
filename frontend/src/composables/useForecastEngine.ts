
import { ref, computed } from 'vue'
import { startOfMonth, addDays, addMonths, format, isBefore, isSameMonth } from 'date-fns'

type RecurringTransaction = {
  label: string
  amount: number
  frequency: 'monthly' | 'weekly'
  nextDueDate: string
}

type AccountHistoryPoint = {
  date: string
  balance: number
}

export function useForecastEngineMock(
  viewType: 'Month' | 'Year',
  recurringTxs: RecurringTransaction[],
  accountHistory: AccountHistoryPoint[],
  manualIncome: number,
  liabilityRate: number
) {
  const today = new Date()
  const startDate = startOfMonth(today)

  const labels = computed(() => {
    if (viewType === 'Month') {
      return Array.from({ length: 30 }, (_, i) =>
        format(addDays(startDate, i), 'MMM d')
      )
    } else {
      return Array.from({ length: 12 }, (_, i) =>
        format(addMonths(startDate, i), 'MMM')
      )
    }
  })

  const forecastLine = computed(() => {
    const length = labels.value.length
    let line = Array(length).fill(0)

    recurringTxs.forEach((tx) => {
      const txDate = new Date(tx.nextDueDate)
      const txInterval = tx.frequency === 'weekly' ? 7 : 30

      for (let i = 0; i < length; i++) {
        const targetDate = viewType === 'Month'
          ? addDays(startDate, i)
          : addMonths(startDate, i)

        if (isBefore(txDate, targetDate) || isSameMonth(txDate, targetDate)) {
          // Roughly deprecate the recurring transaction across interval
          const idx = i
          while (idx < length) {
            line[idx] += tx.amount
            if (tx.frequency === 'weekly') {
              idx += 1 // every week = every 7 days, approximately 1 index per label in month view
            } else {
              idx += viewType === 'Month' ? 4 : 1
            }
          }
        }
      }
    })

    // Apply manual income and liability rate evenly
    const adjustment = (manualIncome || 0) - (liabilityRate || 0)
    line = line.map((val) => val + adjustment)

    return line
  })

  const actualLine = computed(() => {
    const lookup = Object.fromEntries(accountHistory.map(pt => [pt.date, pt.balance]))
    const line = labels.value.map(label => {
      // fallback dummy line: walk upward by 25
      const dateKey = label.includes(' ') ? label : format(new Date(label), 'MMM d')
      return lookup[dateKey] ?? 3000 + Math.random() * 100
    })
    return line
  })

  return {
    labels,
    forecastLine,
    actualLine
  }
}
