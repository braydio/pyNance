/**
 * Planning service for bills and allocations.
 *
 * Provides CRUD operations using Axios to communicate with the backend.
 */
import axios from 'axios'
import type { Bill, Allocation } from '@/types/planning'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Retrieve all bills.
 */
export async function fetchBills(): Promise<Bill[]> {
  const response = await apiClient.get<Bill[]>('/planning/bills')
  return response.data
}

/**
 * Fetch a single bill by identifier.
 *
 * @param id - Bill identifier
 */
export async function fetchBill(id: string): Promise<Bill> {
  const response = await apiClient.get<Bill>(`/planning/bills/${id}`)
  return response.data
}

/**
 * Create a new bill.
 *
 * @param bill - Bill data to create (without id)
 */
export async function createBill(bill: Omit<Bill, 'id'>): Promise<Bill> {
  const response = await apiClient.post<Bill>('/planning/bills', bill)
  return response.data
}

/**
 * Update an existing bill.
 *
 * @param id - Bill identifier
 * @param bill - Partial bill data to update
 */
export async function updateBill(
  id: string,
  bill: Partial<Omit<Bill, 'id'>>,
): Promise<Bill> {
  const response = await apiClient.put<Bill>(`/planning/bills/${id}`, bill)
  return response.data
}

/**
 * Delete a bill.
 *
 * @param id - Bill identifier
 */
export async function deleteBill(id: string): Promise<void> {
  await apiClient.delete(`/planning/bills/${id}`)
}

/**
 * Retrieve allocations for a scenario.
 *
 * @param scenarioId - Scenario identifier
 */
export async function fetchAllocations(
  scenarioId: string,
): Promise<Allocation[]> {
  const response = await apiClient.get<Allocation[]>(
    `/planning/scenarios/${scenarioId}/allocations`,
  )
  return response.data
}

/**
 * Create an allocation for a scenario.
 *
 * @param scenarioId - Scenario identifier
 * @param allocation - Allocation data (without id)
 */
export async function createAllocation(
  scenarioId: string,
  allocation: Omit<Allocation, 'id'>,
): Promise<Allocation> {
  const response = await apiClient.post<Allocation>(
    `/planning/scenarios/${scenarioId}/allocations`,
    allocation,
  )
  return response.data
}

/**
 * Update an allocation within a scenario.
 *
 * @param scenarioId - Scenario identifier
 * @param allocationId - Allocation identifier
 * @param allocation - Partial allocation data to update
 */
export async function updateAllocation(
  scenarioId: string,
  allocationId: string,
  allocation: Partial<Omit<Allocation, 'id'>>,
): Promise<Allocation> {
  const response = await apiClient.put<Allocation>(
    `/planning/scenarios/${scenarioId}/allocations/${allocationId}`,
    allocation,
  )
  return response.data
}

/**
 * Delete an allocation from a scenario.
 *
 * @param scenarioId - Scenario identifier
 * @param allocationId - Allocation identifier
 */
export async function deleteAllocation(
  scenarioId: string,
  allocationId: string,
): Promise<void> {
  await apiClient.delete(
    `/planning/scenarios/${scenarioId}/allocations/${allocationId}`,
  )
}
