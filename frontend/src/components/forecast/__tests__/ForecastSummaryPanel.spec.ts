// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ForecastSummaryPanel from '../ForecastSummaryPanel.vue'

const baseProps = {
  assetBalance: 900,
  liabilityBalance: 500,
  netBalance: 400,
  manualIncome: 120,
  liabilityRate: 40,
  viewType: 'Month',
  includedAccountIds: ['acc-1'],
  excludedAccountIds: [],
  accountOptions: [
    { account_id: 'acc-1', name: 'Checking', institution_name: 'Bank A' },
    { account_id: 'acc-2', name: 'Savings', institution_name: 'Bank B' },
  ],
  computeMeta: {
    lookbackDays: 90,
    movingAverageWindow: 30,
    normalize: false,
    includesAutoDetectedAdjustments: true,
    autoDetectedAdjustmentCount: 2,
  },
}

describe('ForecastSummaryPanel', () => {
  it('emits include/exclude account updates when toggles are clicked', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: baseProps,
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
        ...baseProps,
        includedAccountIds: [],
        excludedAccountIds: ['acc-2'],
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

  it('renders asset, liability, and current balance values with tooltip copy', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...baseProps,
        assetBalance: 2500,
        liabilityBalance: 800,
        netBalance: 1700,
      },
    })

    expect(wrapper.text()).toContain('Assets')
    expect(wrapper.text()).toContain('$2500.00')
    expect(wrapper.text()).toContain('Liabilities')
    expect(wrapper.text()).toContain('$800.00')
    expect(wrapper.text()).toContain('Current Balance')
    expect(wrapper.text()).toContain('$1700.00')
    expect(wrapper.text()).toContain('positive-balance accounts currently included in the forecast')
    expect(wrapper.text()).toContain('Current Balance is assets minus liabilities')
  })

  it('prefers computed forecast net change when provided and explains the calculation inputs', () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        ...baseProps,
        netChange: 123.45,
      },
    })

    expect(wrapper.text()).toContain('Net Delta:')
    expect(wrapper.text()).toContain('123.45')
    expect(wrapper.text()).toContain('30-day moving average')
    expect(wrapper.text()).toContain('latest 90 days of history')
    expect(wrapper.text()).toContain('includes 2 auto-detected adjustments')
  })

  it('updates manual input tooltip copy when the controls change', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: baseProps,
    })

    expect(wrapper.text()).toContain('Manual Income adds $120.00 per day')
    expect(wrapper.text()).toContain('Liability Rate subtracts $40.00 per day')
    expect(wrapper.text()).toContain(
      'classifies that manual control as debt growth from new spending',
    )

    await wrapper.setProps({
      manualIncome: 225,
      liabilityRate: 65,
      viewType: 'Year',
    })

    expect(wrapper.text()).toContain(
      'Manual Income adds $225.00 per day to the projection in Year view',
    )
    expect(wrapper.text()).toContain(
      'Liability Rate subtracts $65.00 per day from the projection in Year view',
    )
  })
})
