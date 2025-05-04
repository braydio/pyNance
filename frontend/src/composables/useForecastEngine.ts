
import { Ref, computed } from 'vue'
import { startOfMonth, addDays, addMonths, format, isBefore, isSameMonth, isAfter } from 'date-fns'

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
  viewType: Ref<'Month' | 'Year'>,
  recurringTxs: RecurringTransaction[],
  accountHistory: AccountHistoryPoint[],
  manualIncome: number,
  liabilityRate: number
) {
  const startDate = computed(() => startOfMonth(new Date()))
  const today = new Date()

  const labels = computed(() => {
    if (viewType.value === 'Month') {
      return Array.from({ length: 30 }, (_, i) =>
        format(addDays(startDate.value, i), 'MMM d')
      )
    } else {
      return Array.from({ length: 12 }, (_, i) =>
        format(addMonths(startDate.value, i), 'MMM')
      )
    }
  })

  const forecastLine = computed(() => {
    const length = labels.value.length
    let line = Array(length).fill(0)

    recurringTxs.forEach((tx) => {
      const txDate = new Date(tx.nextDueDate)

      for (let i = 0; i < length; i++) {
        const targetDate =
          viewType.value === 'Month'
            ? addDays(startDate.value, i)
            : addMonths(startDate.value, i)

        if (isBefore(txDate, targetDate) || isSameMonth(txDate, targetDate)) {
          for (
            let idx = i;
            idx < length;
            idx += tx.frequency === 'weekly' ? 1 : (viewType.value === 'Month' ? 4 : 1)
          ) {
            line[idx] += tx.amount
          }
          break
        }
      }
    })

    const adjustment = (manualIncome || 0) - (liabilityRate || 0)
    return line.map(val => val + adjustment)
  })

  const actualLine = computed(() => {
    const lookup = Object.fromEntries(
      accountHistory.map(pt => [pt.date, pt.balance])
    )

    return labels.value.map((label, idx) => {
      const date = viewType.value === 'Month'
        ? addDays(startDate.value, idx)
        : addMonths(startDate.value, idx)

      if (isAfter(date, today)) {
        return null // hide or make transparent in chart
      }

      return lookup[label] ?? 3000 + Math.random() * 50
    })
  })

  return {
    labels,
    forecastLine,
    actualLine,
  }
}

