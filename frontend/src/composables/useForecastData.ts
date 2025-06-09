// src/composables/useForecastData.ts

import { ref, computed, type Ref } from 'vue'

interface ForecastResponse {
  labels: string[]
  forecast: number[]
  actuals: Array<number | null>
  metadata: Record<string, any>
}

export function useForecastData(
  viewType: Ref<'Month' | 'Year'>,
  manualIncome: Ref<number>,
  liabilityRate: Ref<number>
) {
  const labels = ref<string[]>([])
  const forecast = ref<number[]>([])
  const actuals = ref<Array<number | null>>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const fetchData = async () => {
    loading.value = true
    error.value = null
    try {
      const params = new URLSearchParams({
        view_type: viewType.value,
        manual_income: String(manualIncome.value || 0),
        liability_rate: String(liabilityRate.value || 0)
      })
      const res = await fetch(`/api/forecast?${params.toString()}`)
      if (!res.ok) {
        throw new Error('Failed to fetch forecast data')
      }
      const data: ForecastResponse = await res.json()
      labels.value = data.labels
      forecast.value = data.forecast
      actuals.value = data.actuals
    } catch (err) {
      error.value = err as Error
    } finally {
      loading.value = false
    }
  }

  return {
    labels: computed(() => labels.value),
    forecast: computed(() => forecast.value),
    actuals: computed(() => actuals.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    fetchData
  }
}

