// src/composables/useForecastEngine.ts

import { Ref, computed } from 'vue';
import {
  startOfMonth,
  addDays,
  addMonths,
  format,
  isBefore,
  isSameMonth,
  isAfter,
  parseISO,
} from 'date-fns';

type RecurringTransaction = {
  account_id: string;
  description: string;
  amount: number;
  frequency: 'monthly' | 'weekly';
  next_due_date: string;
};

type AccountHistoryPoint = {
  account_id: string;
  date: string;
  balance: number;
};

export function useForecastEngine(
  viewType: Ref<'Month' | 'Year'>,
  recurringTxs: RecurringTransaction[],
  accountHistory: AccountHistoryPoint[],
  manualIncome: number = 0,
  liabilityRate: number = 0
) {
  const today = new Date();
  const startDate = computed(() => startOfMonth(today));

  const labels = computed(() => {
    if (viewType.value === 'Month') {
      return Array.from({ length: 30 }, (_, i) =>
        format(addDays(startDate.value, i), 'MMM d')
      );
    } else {
      return Array.from({ length: 12 }, (_, i) =>
        format(addMonths(startDate.value, i), 'MMM')
      );
    }
  });

  const forecastLine = computed(() => {
    const length = labels.value.length;
    let line = Array(length).fill(0);

    recurringTxs.forEach((tx) => {
      const txDate = parseISO(tx.next_due_date);
      for (let i = 0; i < length; i++) {
        const targetDate = viewType.value === 'Month'
          ? addDays(startDate.value, i)
          : addMonths(startDate.value, i);

        if (isBefore(txDate, targetDate) || isSameMonth(txDate, targetDate)) {
          for (
            let idx = i;
            idx < length;
            idx += tx.frequency === 'weekly' ? 1 : (viewType.value === 'Month' ? 4 : 1)
          ) {
            line[idx] += tx.amount;
          }
          break;
        }
      }
    });

    const adjustment = (manualIncome || 0) - (liabilityRate || 0);
    return line.map((val) => val + adjustment);
  });

  const actualLine = computed(() => {
    const lookup = Object.fromEntries(
      accountHistory.map((pt) => [
        format(parseISO(pt.date), viewType.value === 'Month' ? 'MMM d' : 'MMM'),
        pt.balance,
      ])
    );

    return labels.value.map((label) => {
      const labelDate = viewType.value === 'Month'
        ? addDays(startDate.value, labels.value.indexOf(label))
        : addMonths(startDate.value, labels.value.indexOf(label));

      return isAfter(labelDate, today) ? null : lookup[label] ?? null;
    });
  });

  return {
    labels,
    forecastLine,
    actualLine
  };
}

