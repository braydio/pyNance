// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ForecastSummaryPanel from '../ForecastSummaryPanel.vue'

describe('ForecastSummaryPanel', () => {
  it('emits include/exclude account updates when toggles are clicked', async () => {
    const wrapper = mount(ForecastSummaryPanel, {
      props: {
        currentBalance: 400,
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
})
