
export const mockAccountHistory = Array.from({ length: 30 }, (_, i) => {
  const d = new Date()
  d.setDate(d.getDate() - (29 - i))
  return {
    date: d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    balance: 4000 + i * 25 + Math.random() * 30,
  }
})
