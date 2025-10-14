// frontend/src/utils/planning.ts

/**
 * Utilities supporting the Planning feature.
 *
 * The helpers in this module normalise form state, ensure allocation
 * percentages remain within constraints, and bridge the persisted
 * planning schema with UI-friendly drafts.
 */

import type {
  Allocation,
  Bill,
  BillFrequency,
  BillOrigin,
} from '@/types/planning'

/**
 * Reactive draft shape used by {@link BillForm}.
 */
export interface BillFormState {
  id?: string
  name: string
  amount: string
  dueDate: string
  frequency: BillFrequency | ''
  category: string
  scenarioId?: string
  accountId?: string
  origin?: BillOrigin
}

/**
 * Payload emitted from {@link BillForm} once validation succeeds.
 */
export interface BillFormSubmitPayload {
  id?: string
  name: string
  amountCents: number
  dueDate: string
  frequency: BillFrequency
  category: string
  scenarioId?: string
  accountId?: string
  origin?: BillOrigin
}

/**
 * Convert a persisted {@link Bill} into an editable draft.
 */
export function billToFormState(bill?: Bill | null): BillFormState {
  if (!bill) {
    return {
      name: '',
      amount: '',
      dueDate: '',
      frequency: '',
      category: '',
    }
  }

  return {
    id: bill.id,
    name: bill.name,
    amount: centsToAmountString(bill.amountCents),
    dueDate: bill.dueDate,
    frequency: bill.frequency,
    category: bill.category ?? '',
    scenarioId: bill.scenarioId,
    accountId: bill.accountId,
    origin: bill.origin,
  }
}

/**
 * Convert a {@link BillFormState} into a payload ready for persistence.
 *
 * @throws {Error} when the amount cannot be parsed or when the frequency is missing.
 */
export function normaliseBillForm(
  draft: BillFormState,
  previous?: Bill | null,
): BillFormSubmitPayload {
  const amountValue = parseCurrencyInput(draft.amount)
  if (!Number.isFinite(amountValue) || amountValue <= 0) {
    throw new Error('Invalid amount')
  }

  const frequency = draft.frequency || previous?.frequency
  if (!frequency) {
    throw new Error('Missing bill frequency')
  }

  const amountCents = Math.round(amountValue * 100)

  return {
    id: draft.id ?? previous?.id,
    name: draft.name.trim(),
    amountCents,
    dueDate: draft.dueDate,
    frequency,
    category: draft.category.trim(),
    scenarioId: draft.scenarioId ?? previous?.scenarioId,
    accountId: draft.accountId ?? previous?.accountId,
    origin: draft.origin ?? previous?.origin,
  }
}

/**
 * Parse a user supplied currency value.
 */
export function parseCurrencyInput(value: string): number {
  const sanitized = value.replace(/[^0-9.-]/g, '')
  const parsed = Number.parseFloat(sanitized)
  return Number.isFinite(parsed) ? parsed : NaN
}

/**
 * Convert an amount in cents to a decimal string with two fraction digits.
 */
export function centsToAmountString(cents?: number): string {
  if (cents == null) return ''
  return (cents / 100).toFixed(2)
}

/**
 * Clamp the allocation for a specific category while respecting the overall cap.
 */
export function clampAllocations(
  allocations: Record<string, number>,
  category: string,
  nextValue: number,
  cap = 100,
): {
  next: Record<string, number>
  total: number
} {
  const sanitized = sanitizePercent(nextValue)

  const totalWithoutCategory = Object.entries(allocations)
    .filter(([key]) => key !== category)
    .reduce((sum, [, value]) => sum + sanitizePercent(value), 0)

  const allowed = Math.min(sanitized, Math.max(cap - totalWithoutCategory, 0))
  const next = { ...allocations, [category]: allowed }
  const total = totalWithoutCategory + allowed
  return { next, total }
}

/**
 * Build a mutable mapping of percent allocations for use with the allocator UI.
 */
export function allocationsToPercentMap(
  allocations: Allocation[],
): Record<string, number> {
  return allocations
    .filter((allocation) => allocation.kind === 'percent')
    .reduce<Record<string, number>>((acc, allocation) => {
      acc[allocation.target] = sanitizePercent(allocation.value)
      return acc
    }, {})
}

/**
 * Merge percent allocation updates back into the canonical allocation list.
 */
export function mergePercentAllocations(
  allocations: Allocation[],
  percentages: Record<string, number>,
  idFactory: () => string,
): Allocation[] {
  const fixedAllocations = allocations.filter((allocation) => allocation.kind !== 'percent')
  const percentEntries = Object.entries(percentages).map<Allocation>(([target, value]) => {
    const existing = allocations.find(
      (allocation) => allocation.kind === 'percent' && allocation.target === target,
    )

    return {
      id: existing?.id ?? idFactory(),
      target,
      kind: 'percent',
      value: sanitizePercent(value),
    }
  })

  return [...fixedAllocations, ...percentEntries]
}

/**
 * Normalise a number into the 0-100 percentage domain.
 */
export function sanitizePercent(value: number): number {
  const parsed = Math.round(Number(value) || 0)
  return Math.min(100, Math.max(parsed, 0))
}
