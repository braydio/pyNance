
// Composable utility to generate consistent date ranges and boundaries

export function useDateRange(viewType) {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const day = today.getDate()

  const labels = viewType === 'Year'
    ? Array.from({ length: 12 }, (_, i) =>
        new Date(year, i).toLocaleString('default', { month: 'short' })
      )
    : Array.from({ length: new Date(year, month + 1, 0).getDate() }, (_, i) =>
        `${month + 1}/${i + 1}`
      )

  const scopeLength = viewType === 'Year' ? month + 1 : day

  return {
    today,
    currentMonth: month,
    currentDay: day,
    labels,
    scopeLength // How far we are into the year/month
  }
}
