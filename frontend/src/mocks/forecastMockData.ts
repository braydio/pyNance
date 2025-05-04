// frontend/src/mocks/forecastMockData.ts

export const mockRecurringTransactions = [
  {
    label: 'Salary',
    amount: 3000,
    frequency: 'monthly',
    nextDueDate: new Date().toISOString(),
  },
  {
    label: 'Gym Membership',
    amount: -50,
    frequency: 'monthly',
    nextDueDate: new Date().toISOString(),
  },
  {
    label: 'Streaming Service',
    amount: -15,
    frequency: 'monthly',
    nextDueDate: new Date().toISOString(),
  },
  {
    label: 'Loan Payment',
    amount: -400,
    frequency: 'monthly',
    nextDueDate: new Date().toISOString(),
  },
]

export const mockAccountHistory = Array.from({ length: 30 }, (_, i) => {
  const d = new Date()
  d.setDate(d.getDate() - (29 - i))
  return {
    date: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    balance: 4000 + i * 25 + Math.random() * 30,
  }
})

