// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { useDashboardModals } from '../useDashboardModals'

describe('useDashboardModals', () => {
  it('defaults to none and exposes visibility flags', () => {
    const { currentModal, visibility } = useDashboardModals()

    expect(currentModal.value).toBe('none')
    expect(visibility.value).toEqual({
      daily: false,
      category: false,
      accounts: false,
      transactions: false,
    })
  })

  it('activates a single modal at a time', () => {
    const { currentModal, openModal, visibility } = useDashboardModals()

    openModal('daily')
    expect(currentModal.value).toBe('daily')
    expect(visibility.value.daily).toBe(true)

    openModal('accounts')
    expect(currentModal.value).toBe('accounts')
    expect(visibility.value).toMatchObject({
      daily: false,
      accounts: true,
      category: false,
      transactions: false,
    })
  })

  it('closes only the active modal when specified', () => {
    const { currentModal, openModal, closeModal, visibility } = useDashboardModals()

    openModal('transactions')
    closeModal('daily')
    expect(currentModal.value).toBe('transactions')

    closeModal('transactions')
    expect(currentModal.value).toBe('none')
    expect(visibility.value.transactions).toBe(false)
  })

  it('resets all modals when closing without a target', () => {
    const { currentModal, openModal, closeModal, visibility } = useDashboardModals('category')

    expect(visibility.value.category).toBe(true)
    closeModal()
    expect(currentModal.value).toBe('none')
    expect(visibility.value).toMatchObject({
      daily: false,
      category: false,
      accounts: false,
      transactions: false,
    })
  })

  it('exposes dedicated visibility refs for each modal', () => {
    const { currentModal, openModal, isVisible } = useDashboardModals()

    expect(isVisible('daily').value).toBe(false)
    openModal('transactions')
    expect(isVisible('transactions').value).toBe(true)
    expect(isVisible('daily').value).toBe(false)

    currentModal.value = 'invalid' as any
    expect(isVisible('daily').value).toBe(false)
  })
})
