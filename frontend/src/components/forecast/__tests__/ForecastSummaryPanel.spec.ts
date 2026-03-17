// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ForecastSummaryPanel from '../ForecastSummaryPanel.vue'

describe('ForecastSummaryPanel', () => {
  it('emits include/exclude account updates when toggles are clicked', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        assetBalance: 900,
        liabilityBalance: 500,
        netBalance: 400,
        manualIncome: 0,
        liabilityRate: 0,
        viewType: 'Month',
        includedAccountIds: ['acc-1'],
        excludedAccountIds: [],
        accountOptions: [
          { account_id: 'acc-1', name: 'Checking', institution_name: 'Bank A' },
          { account_id: 'acc-2', name: 'Savings', institution_name: 'Bank B' },
        ],
      },
    })

    await wrapper.get('.value-link').trigger('click')
    const excludeChips = wrapper.findAll('.selector-item .chip-exclude')
    await excludeChips[1].trigger('click')

    const includedEvents = wrapper.emitted('update:includedAccountIds')
    const excludedEvents = wrapper.emitted('update:excludedAccountIds')

    expect(includedEvents).toBeTruthy()
    expect(excludedEvents).toBeTruthy()
    expect(includedEvents?.at(-1)?.[0]).toEqual(['acc-1'])
    expect(excludedEvents?.at(-1)?.[0]).toEqual(['acc-2'])
  })

  it('applies dashboard group shortcut as include selection', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        assetBalance: 1200,
        liabilityBalance: 700,
        netBalance: 500,
        manualIncome: 0,
        liabilityRate: 0,
        viewType: 'Month',
        includedAccountIds: [],
        excludedAccountIds: ['acc-2'],
        accountOptions: [
          { account_id: 'acc-1', name: 'Checking', institution_name: 'Bank A' },
          { account_id: 'acc-2', name: 'Savings', institution_name: 'Bank B' },
        ],
        accountGroupOptions: [
          { id: 'group-1', name: 'Core accounts', accountIds: ['acc-1', 'acc-2'] },
        ],
      },
    })

    await wrapper.get('.selector-toggle').trigger('click')
    await wrapper.get('.shortcut-chip').trigger('click')

    expect(wrapper.emitted('update:includedAccountIds')?.at(-1)?.[0]).toEqual(['acc-1', 'acc-2'])
    expect(wrapper.emitted('update:excludedAccountIds')?.at(-1)?.[0]).toEqual([])
  })

  it('renders asset, liability, and net balances', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        assetBalance: 2500,
        liabilityBalance: 800,
        netBalance: 1700,
        manualIncome: 0,
        liabilityRate: 0,
        viewType: 'Month',
        includedAccountIds: [],
        excludedAccountIds: [],
        accountOptions: [],
      },
    })

    expect(wrapper.text()).toContain('Assets')
    expect(wrapper.text()).toContain('$2500.00')
    expect(wrapper.text()).toContain('Liabilities')
    expect(wrapper.text()).toContain('$800.00')
    expect(wrapper.text()).toContain('Net')
    expect(wrapper.text()).toContain('$1700.00')
  })

  it('prefers computed forecast net change when provided', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        assetBalance: 900,
        liabilityBalance: 500,
        netBalance: 400,
        manualIncome: 0,
        liabilityRate: 0,
        netChange: 123.45,
        viewType: 'Month',
        includedAccountIds: [],
        excludedAccountIds: [],
        accountOptions: [],
      },
    })

    expect(wrapper.text()).toContain('Net Delta:')
    expect(wrapper.text()).toContain('123.45')
  })
})
