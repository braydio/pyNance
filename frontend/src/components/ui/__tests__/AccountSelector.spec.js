// @vitest-environment jsdom
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AccountSelector from '../AccountSelector.vue'

const accounts = [
  { id: 'chk', name: 'Checking', type: 'depository', balance: -25 }, // overdrawn asset
  { id: 'cc', name: 'Card', type: 'credit', balance: 40 }, // positive number on a liability
  { id: 'brk', name: 'Brokerage', type: 'brokerage', is_investment: true, balance: 1000 },
]

const mountSelector = (props = {}) =>
  mount(AccountSelector, {
    props: { selectedAccountIds: ['chk'], availableAccounts: accounts, ...props },
  })

describe('AccountSelector', () => {
  it('uses keyboard-operable checkboxes inside labels, with checked state', async () => {
    const wrapper = mountSelector()
    const boxes = wrapper.findAll('input[type="checkbox"].account-card__input')
    expect(boxes).toHaveLength(3)
    expect(wrapper.get('[data-testid="account-card-chk"]').element.tagName).toBe('LABEL')
    expect(boxes[0].element.checked).toBe(true)
    expect(boxes[1].element.checked).toBe(false)
    await boxes[1].setValue(true)
    expect(wrapper.emitted('toggle-account')[0]).toEqual(['cc'])
  })

  it('classifies assets and liabilities by account type, not by balance sign', () => {
    const wrapper = mountSelector()
    const label = (id) => wrapper.get(`[data-testid="account-card-${id}"] .balance-label`).text()
    expect(label('chk')).toBe('Asset') // negative balance, still a deposit account
    expect(label('cc')).toBe('Liability') // positive number, still a credit account
    expect(label('brk')).toBe('Asset')
    expect(wrapper.get('[data-testid="account-card-cc"]').classes()).toContain('liability')
  })

  it('keeps quick actions as non-submitting buttons that emit', async () => {
    const wrapper = mountSelector()
    wrapper
      .findAll('.quick-actions button')
      .forEach((b) => expect(b.attributes('type')).toBe('button'))
    await wrapper.findAll('.quick-actions button')[0].trigger('click')
    expect(wrapper.emitted('select-all')).toHaveLength(1)
  })
})
